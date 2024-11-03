#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ARRAY_SIZE 1024*1024  // 1MB array
#define ITERATIONS 100

void memory_intensive_task(int* array, int size, const char* thread_name) {
    printf("%s starting memory operations\n", thread_name);
    
    for(int i = 0; i < ITERATIONS; i++) {
        // Write operation
        for(int j = 0; j < size; j++) {
            array[j] = j + i;
        }
        
        // Read operation
        int sum = 0;
        for(int j = 0; j < size; j++) {
            sum += array[j];
        }
        
        if (i % 10 == 0) {
            printf("%s completed iteration %d, sum: %d\n", thread_name, i, sum);
        }
    }
    
    printf("%s completed all iterations\n", thread_name);
}

int main() {
    printf("QoS Test Program Starting\n");
    
    // Allocate memory for arrays
    int* array1 = (int*)malloc(ARRAY_SIZE * sizeof(int));
    int* array2 = (int*)malloc(ARRAY_SIZE * sizeof(int));
    
    if (!array1 || !array2) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    // Perform memory operations
    memory_intensive_task(array1, ARRAY_SIZE, "Thread-1");
    memory_intensive_task(array2, ARRAY_SIZE, "Thread-2");
    
    // Cleanup
    free(array1);
    free(array2);
    
    printf("QoS Test Program Completed\n");
    return 0;
}