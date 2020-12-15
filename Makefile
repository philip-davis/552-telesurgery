all: patient

patient: patient.o
	gcc -g -o patient patient.o -lpthread

patient.o: patient.c
	gcc -g -c patient.c

clean:
	rm *\.o patient
