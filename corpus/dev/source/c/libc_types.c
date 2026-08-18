/* Functions whose types come from the C library, not from this file.
 *
 * The rest of the C corpus is self-contained: every struct it names is
 * declared in the same translation unit, so a decompiler's type library has
 * nothing to recognize and its firing rate is zero by construction. That
 * makes library-driven type recovery unmeasurable, not good or bad.
 *
 * Every function here takes or builds a type the library knows -- FILE, time_t,
 * struct tm, div_t, size_t -- so DWARF ground truth carries those names and a
 * decompiler that recovers them can be scored for it.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* FILE * through a parameter: the type is only knowable from the callee. */
long file_size(FILE *fp)
{
    long here = ftell(fp);
    fseek(fp, 0, SEEK_END);
    long end = ftell(fp);
    fseek(fp, here, SEEK_SET);
    return end;
}

/* FILE * as a return value, plus a char * path argument. */
FILE *open_reader(const char *path)
{
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) {
        return NULL;
    }
    setvbuf(fp, NULL, _IOFBF, 4096);
    return fp;
}

/* size_t from strlen, and a char * walked as a string. */
size_t count_spaces(const char *s)
{
    size_t n = 0;
    size_t len = strlen(s);
    for (size_t i = 0; i < len; i++) {
        if (s[i] == ' ') {
            n++;
        }
    }
    return n;
}

/* struct tm read through a pointer, with int fields at known offsets. */
int tm_year_of(const struct tm *t)
{
    return t->tm_year + 1900;
}

/* struct tm built locally: a stack slot whose layout the library knows. */
int days_between(time_t a, time_t b)
{
    double secs = difftime(b, a);
    return (int)(secs / 86400.0);
}

/* div_t returned by value -- a two-int aggregate from the library. */
int quotient_of(int num, int den)
{
    div_t d = div(num, den);
    return d.quot + d.rem;
}

/* void * from malloc, used as a typed buffer and freed. */
int *make_range(int n)
{
    int *p = (int *)malloc((size_t)n * sizeof(int));
    if (p == NULL) {
        return NULL;
    }
    for (int i = 0; i < n; i++) {
        p[i] = i;
    }
    return p;
}

/* memcpy/memset: the classic prototype-propagation targets. */
void copy_prefix(char *dst, const char *src, size_t n)
{
    memset(dst, 0, n + 1);
    memcpy(dst, src, n);
}

/* fgets into a caller buffer, returning the library's own char *. */
char *read_line(FILE *fp, char *buf, int cap)
{
    char *got = fgets(buf, cap, fp);
    if (got == NULL) {
        return NULL;
    }
    size_t len = strlen(got);
    if (len > 0 && got[len - 1] == '\n') {
        got[len - 1] = '\0';
    }
    return got;
}

/* strtol's char ** endptr: a pointer-to-pointer the library defines. */
long parse_prefix(const char *s, int base)
{
    char *end = NULL;
    long v = strtol(s, &end, base);
    if (end == s) {
        return -1;
    }
    return v;
}

/* Keeps every function above reachable so no linker drops one, and gives the
 * PE target the entry point it needs. Not itself a benchmark target. */
int main(void)
{
    char buf[64];
    FILE *fp = open_reader("libc_types.c");
    if (fp != NULL) {
        (void)file_size(fp);
        (void)read_line(fp, buf, (int)sizeof buf);
        fclose(fp);
    }
    copy_prefix(buf, "hello world", 5);
    time_t now = time(NULL);
    struct tm *lt = localtime(&now);
    int total = (int)count_spaces("a b c")
              + (lt ? tm_year_of(lt) : 0)
              + days_between(now, now + 86400)
              + quotient_of(17, 5)
              + (int)parse_prefix("0x2a", 16);
    int *r = make_range(4);
    if (r != NULL) {
        total += r[3];
        free(r);
    }
    printf("%d\n", total);
    return 0;
}
