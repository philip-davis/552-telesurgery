/*
 * https://elixir.bootlin.com/linux/v4.2/source/Documentation/networking/timestamping/timestamping.c
 * https://github.com/majek/openonload/blob/master/src/tests/onload/hwtimestamping/tx_timestamping.c
 **/

#include<assert.h>
#include<errno.h>
#include<pthread.h>
#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<unistd.h>

#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <net/if.h>

#include <linux/net_tstamp.h>
#include <linux/sockios.h>
#include <linux/errqueue.h>

pthread_barrier_t barrier;

struct vs_opts {
    char *interface;
    int port;
    int dgram_payload;
    int frame_size;
    int nframes;
    int tos;
};

struct vstream {
    int sock;
    struct vs_opts *opts;
    int packet_id;
    char ctrlp[16];
    char *padp;
    struct sockaddr s_addr;
};

struct seq_ts {
    int seq;
    struct timeval tstamp;
};

int init_socket(const char *interface, int port)
{
    int sock;
    struct ifreq device = {0};
    struct ifreq hwtstamp = {0};
    struct hwtstamp_config hwconfig = {0};
    int ts_flags;
    struct sockaddr_in addr;
    int tos = 0x16;

    // enable timestamps on socket
    ts_flags = SOF_TIMESTAMPING_TX_HARDWARE | SOF_TIMESTAMPING_RAW_HARDWARE;
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if(sock == -1) {
        perror("sock");
        exit(-1);
    }

    // get interface IP
    setsockopt(sock, SOL_SOCKET, SO_TIMESTAMPING, &ts_flags, sizeof(ts_flags));
    strncpy(device.ifr_name, interface, sizeof(device.ifr_name));
    if(ioctl(sock, SIOCGIFADDR, &device) < 0) {
        perror("ip addr");
        exit(-1);
    }

    // enable timestamps on device
    strncpy(hwtstamp.ifr_name, interface, sizeof(hwtstamp.ifr_name));
    hwtstamp.ifr_data = (void *)&hwconfig;
    hwconfig.tx_type = HWTSTAMP_TX_ON;
    hwconfig.rx_filter =  HWTSTAMP_FILTER_NONE;
    if(ioctl(sock, SIOCSHWTSTAMP, &hwtstamp) < 0) {
        perror("ioctl");
        exit(-1);
    }

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);

    //set TOS
    setsockopt(sock, IPPROTO_IP, IP_TOS, &tos, sizeof(tos));

    if(bind(sock, (struct sockaddr *)&addr, sizeof(struct sockaddr_in)) < 0) {
        perror("bind");
        exit(-1);
    }

    return(sock);
}

void send_frame_header(struct vstream *vs, int frame_id, int num_pad_packets)
{
    int seq = vs->packet_id++;

    printf("%d\n", frame_id); 
    memcpy(&vs->ctrlp[0], &seq, 4);
    memcpy(&vs->ctrlp[4], &frame_id, 4);
    memcpy(&vs->ctrlp[8], &num_pad_packets, 4);
    memcpy(&vs->ctrlp[12], &vs->opts->frame_size, 4);

    sendto(vs->sock, vs->ctrlp, 16, 0, &vs->s_addr, sizeof(vs->s_addr));
}

void send_payload_dgram(struct vstream *vs, int frame_id, int frame_seq, int num_pad_packets)
{
    int seq = vs->packet_id++;

    memcpy(&vs->padp[0], &seq, 4);
    memcpy(&vs->padp[4], &frame_id, 4);
    memcpy(&vs->padp[8], &frame_seq, 4);
    memcpy(&vs->padp[12], &num_pad_packets, 4);

    sendto(vs->sock, vs->padp, 16 + vs->opts->dgram_payload, 0, &vs->s_addr, sizeof(vs->s_addr));    
}

void send_frame(struct vstream *vs, int frame_id)
{
    int num_pad_packets;
    int i;    

    num_pad_packets = vs->opts->frame_size / vs->opts->dgram_payload;
    send_frame_header(vs, frame_id, num_pad_packets);

    for(i = 0; i < num_pad_packets; i++) {
        send_payload_dgram(vs, frame_id, i, num_pad_packets);
    }
}

long get_wait_usec(struct timeval *stime, int frame_id)
{
    struct timeval due, curr;
    long wait_usec;

    due.tv_usec = stime->tv_usec + (33000 * frame_id);
    due.tv_sec = stime->tv_sec + (due.tv_usec / 1000000);
    due.tv_usec %= 1000000;

    gettimeofday(&curr, NULL);
    wait_usec  = 1000000 * (due.tv_sec - curr.tv_sec);
    wait_usec += due.tv_usec - curr.tv_usec;

    return(wait_usec);

}

static int extract_tstamp(struct msghdr *msg, int res,
        char *data,
        int sock, int recvmsg_flags, struct timespec *result)
{
    struct cmsghdr *cmsg;
    int seq;

    for (cmsg = CMSG_FIRSTHDR(msg);
            cmsg;
            cmsg = CMSG_NXTHDR(msg, cmsg)) {
        if(cmsg->cmsg_level == SOL_SOCKET && cmsg->cmsg_type == SO_TIMESTAMPING) {
            *result = *(((struct timespec *)CMSG_DATA(cmsg))+2);
            seq = *((uint32_t *)&data[42]);
            break;
        }
    }
    //printf("seq %d: %ld.%09ld\n", seq, (long)result->tv_sec, (long)result->tv_nsec);

    return seq;
} 

static int recvpacket(int sock, int recvmsg_flags, struct timespec *tstamp)
{
    char data[256];
    struct msghdr msg;
    struct iovec entry;
    struct sockaddr_in from_addr;
    struct {
        struct cmsghdr cm;
        char control[512];
    } control;
    struct cmsghdr *cmsg;
    int res;

    memset(&msg, 0, sizeof(msg));
    msg.msg_iov = &entry;
    msg.msg_iovlen = 1;
    entry.iov_base = data;
    entry.iov_len = sizeof(data);
    msg.msg_name = (caddr_t)&from_addr;
    msg.msg_namelen = sizeof(from_addr);
    msg.msg_control = &control;
    msg.msg_controllen = sizeof(control);

    res = recvmsg(sock, &msg, recvmsg_flags|MSG_DONTWAIT);
    if(res > 0) {
        return(extract_tstamp(&msg, res, data, 
                    sock, recvmsg_flags, tstamp));
    }
}

void *run_video_stream(void *optsv)
{
    struct vstream vs = {0};
    char recvbuf[4096];
    ssize_t recvlen;
    struct timeval start_time;
    int addrlen;
    int wait_usec;
    int ts_seq;
    struct timespec tstamp;
    int npackets;
    struct timespec *ts_results;
    int i;

    vs.opts = (struct vs_opts *)optsv;

    npackets = vs.opts->nframes * (1 + vs.opts->frame_size / vs.opts->dgram_payload);
    printf("%d packets total in the stream.\n", npackets);
    ts_results = calloc(npackets, sizeof(*ts_results));    

    vs.sock = init_socket(vs.opts->interface, vs.opts->port);

    vs.padp = malloc(vs.opts->dgram_payload + 16);
    memset(&vs.padp[16], 0x5a, vs.opts->dgram_payload);

    printf("waiting for surgeon\n");
    addrlen = sizeof(struct sockaddr_in);
    recvlen = recvfrom(vs.sock, recvbuf, 4096, 0, &vs.s_addr, &addrlen);

    pthread_barrier_wait(&barrier);
    gettimeofday(&start_time, NULL);
    for(i = 0; i < vs.opts->nframes; i++) {
        pthread_barrier_wait(&barrier);
        send_frame(&vs, i);
        do {
            wait_usec = get_wait_usec(&start_time, i);
            if(wait_usec > 0) {
                ts_seq = recvpacket(vs.sock, MSG_ERRQUEUE, &tstamp);
                if(ts_seq >= 0) {
                    ts_results[ts_seq] = tstamp;          
                }
            }   
        } while(wait_usec > 0);
    }
    send_frame_header(&vs, vs.opts->nframes, 0); 

    close(vs.sock);
    free(vs.padp);
    pthread_exit(ts_results);
}

int main(int argc, char **argv)
{
    size_t dgram_payload = 1000;
    size_t frame_size = 80000;
    int nframes = 300;
    int tos = 0;
    struct vs_opts l_opts, r_opts;
    pthread_t l_thread, r_thread;
    struct timespec *l_results, *r_results;
    int npackets;
    FILE *resfile;
    int i;

    l_opts.port = 5555;
    r_opts.port = 5556;
    l_opts.dgram_payload = r_opts.dgram_payload = dgram_payload;
    l_opts.frame_size = r_opts.frame_size = frame_size;
    l_opts.nframes = r_opts.nframes = nframes;
    l_opts.tos = r_opts.tos = tos;

    if(argc < 3) {
        fprintf(stderr, "usage: patient <interface> <result_file>\n");
        return(-1);
    }

    pthread_barrier_init(&barrier, NULL, 2);

    l_opts.interface = strdup(argv[1]);
    r_opts.interface = strdup(argv[1]);

    pthread_create(&l_thread, NULL, run_video_stream, &l_opts);
    pthread_create(&r_thread, NULL, run_video_stream, &r_opts);

    pthread_join(l_thread, (void **)&l_results);
    pthread_join(r_thread, (void **)&r_results);;

    npackets = nframes * (1 + (frame_size / dgram_payload));

    resfile = fopen(argv[2], "w");
    for(i = 0; i < npackets; i++) {
        fprintf(resfile, "%d,%ld.%09ld,%ld.%09ld\n", i, l_results[i].tv_sec, l_results[i].tv_nsec, r_results[i].tv_sec, r_results[i].tv_nsec);
    }

    fclose(resfile);

    free(l_results);
    free(r_results);

    return 0;
}
