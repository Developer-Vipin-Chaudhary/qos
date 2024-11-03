#include <stdio.h>
#include <stdlib.h>

#define ARRAY_SIZE (1024*64)  // Smaller array for SE mode
#define ITERATIONS 50

__attribute__((noinline))
void memory_task(int cpu_id) {
    volatile int* array = (volatile int*)malloc(ARRAY_SIZE * sizeof(int));
    if (!array) return;

    printf("CPU %d starting memory operations\n", cpu_id);
    
    for (int i = 0; i < ITERATIONS; i++) {
        for (int j = 0; j < ARRAY_SIZE; j++) {
            array[j] = j + i;  // Write
        }
        
        int sum = 0;
        for (int j = 0; j < ARRAY_SIZE; j++) {
            sum += array[j];   // Read
        }
        
        printf("CPU %d - Iteration %d: Sum = %d\n", cpu_id, i, sum);
    }
    
    free((void*)array);
}

int main(int argc, char *argv[]) {
    int cpu_id = (argc > 1) ? atoi(argv[1]) : 0;
    memory_task(cpu_id);
    return 0;
}
