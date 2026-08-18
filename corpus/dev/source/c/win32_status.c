/* Functions that traffic in Win32 status and error codes.
 *
 * The corpus otherwise contains no Windows API use at all: scanning 447
 * decompiled functions for the 3,155 distinctive values in Fission's Win32
 * constant table finds zero occurrences. Constant-name recovery is therefore
 * unmeasurable here, the same way library type recovery was before
 * libc_types.c.
 *
 * Every function below either returns a documented code, compares against one,
 * or passes one to an API, so a decompiler that names them can be scored and
 * one that names the wrong thing can be caught.
 */
#include <windows.h>

/* GetLastError compared against a distinctive ERROR_* value. */
int open_missing_is_not_found(const char *path)
{
    HANDLE h = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL,
                           OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h != INVALID_HANDLE_VALUE) {
        CloseHandle(h);
        return 0;
    }
    return GetLastError() == ERROR_FILE_NOT_FOUND;
}

/* Returns an HRESULT-shaped code directly. */
long buffer_too_small(unsigned long need, unsigned long have)
{
    if (need > have) {
        return (long)0x8007007A; /* HRESULT_FROM_WIN32(ERROR_INSUFFICIENT_BUFFER) */
    }
    return 0;
}

/* Distinctive protection constants passed to an API. */
void *reserve_guarded(unsigned long size)
{
    void *p = VirtualAlloc(NULL, size, MEM_RESERVE | MEM_COMMIT,
                           PAGE_EXECUTE_READWRITE);
    if (p == NULL) {
        return NULL;
    }
    unsigned long old = 0;
    VirtualProtect(p, size, PAGE_NOACCESS, &old);
    return p;
}

/* A switch over several distinctive error codes. */
const char *describe_error(unsigned long code)
{
    switch (code) {
    case ERROR_ACCESS_DENIED:
        return "denied";
    case ERROR_INVALID_HANDLE:
        return "handle";
    case ERROR_NOT_ENOUGH_MEMORY:
        return "memory";
    case ERROR_SHARING_VIOLATION:
        return "sharing";
    default:
        return "other";
    }
}

/* Registry API returning ERROR_SUCCESS rather than a BOOL. */
int probe_registry_key(void)
{
    HKEY key;
    long rc = RegOpenKeyExA(HKEY_LOCAL_MACHINE,
                            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion",
                            0, KEY_READ, &key);
    if (rc != ERROR_SUCCESS) {
        return -1;
    }
    RegCloseKey(key);
    return 0;
}

/* Wait codes, which are distinctive and easy to confuse with small ints. */
int wait_for_one(void *handle, unsigned long ms)
{
    unsigned long rc = WaitForSingleObject(handle, ms);
    if (rc == WAIT_TIMEOUT) {
        return 1;
    }
    if (rc == WAIT_ABANDONED) {
        return 2;
    }
    return 0;
}

int main(void)
{
    int total = open_missing_is_not_found("nope.txt")
              + (int)buffer_too_small(64, 16)
              + (reserve_guarded(4096) != NULL)
              + (int)describe_error(ERROR_ACCESS_DENIED)[0]
              + probe_registry_key()
              + wait_for_one(GetCurrentProcess(), 0);
    return total;
}
