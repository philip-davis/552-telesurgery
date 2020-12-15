/*
 * https://elixir.bootlin.com/linux/v4.2/source/Documentation/networking/timestamping/timestamping.c
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

int init_socket(const char *interface, int port)
{
    int sock;
    struct ifreq device = {0};
    struct ifreq hwtstamp = {0};
    struct hwtstamp_config hwconfig = {0};
    int ts_flags;
    struct sockaddr_in addr;
    
    // enable timestamps on socket
    ts_flags = SOF_TIMESTAMPING_TX_HARDWARE;
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
    /*
    strncpy(hwtstamp.ifr_name, interface, sizeof(hwtstamp.ifr_name));
    hwtstamp.ifr_data = (void *)&hwconfig;
    hwconfig.tx_type = HWTSTAMP_TX_ON;
    hwconfig.rx_filter =  HWTSTAMP_FILTER_NONE;
    if(ioctl(sock, SIOCSHWTSTAMP, &hwtstamp) < 0) {
        perror("ioctl");
        exit(-1);
    }
    */

    addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = htonl(INADDR_ANY);
	addr.sin_port = htons(port);

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

static void recvpacket(int sock, int recvmsg_flags)
{
    char data[256];
	struct msghdr msg;
	struct iovec entry;
	struct sockaddr_in from_addr;
	struct {
		struct cmsghdr cm;
		char control[512];
	} control;
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
	printf("%d\n", res);    
}

void *run_video_stream(void *optsv)
{
    struct vstream vs = {0};
    char recvbuf[4096];
    ssize_t recvlen;
    struct timeval start_time;
    int addrlen;
    int wait_usec;
    int i;

    vs.opts = (struct vs_opts *)optsv;

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
    			recvpacket(vs.sock, MSG_ERRQUEUE);            
            }   
        }while(wait_usec > 0);
    }
    send_frame_header(&vs, vs.opts->nframes, 0);
    close(vs.sock);

    free(vs.padp);
    pthread_exit(NULL);
}

int main(int argc, char **argv)
{
    struct vs_opts l_opts = {
        .port = 5555,
        .dgram_payload = 1000,
        .frame_size = 80000,
        .nframes = 300,
        .tos = 0
    };
    struct vs_opts r_opts = {
        .port = 5556,
        .dgram_payload = 1000,
        .frame_size = 80000,
        .nframes = 300,
        .tos = 0
    };
    pthread_t l_thread, r_thread;

    if(argc < 2) {
        fprintf(stderr, "usage: patient <interface>\n");
        return(-1);
    }

    pthread_barrier_init(&barrier, NULL, 2);

    l_opts.interface = strdup(argv[1]);
    r_opts.interface = strdup(argv[1]);

    pthread_create(&l_thread, NULL, run_video_stream, &l_opts);
    pthread_create(&r_thread, NULL, run_video_stream, &r_opts);
 
    pthread_join(l_thread, NULL);
    pthread_join(r_thread, NULL);
   
    return 0;
}
