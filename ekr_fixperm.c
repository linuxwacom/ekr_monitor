/**
 * Copyright (C) 2018 by Jason Gerecke, Wacom. <jason.gerecke@wacom.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#include <glob.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>

#define HZ_LOWER            1
#define HZ_UPPER            1000
#define HZ_DEFAULT          5
#define HZ_TO_NSEC(hz)      (1000000000l/(hz))
#define NSEC_TO_TIMESPEC(t) { (t) / 1000000000l, (t) % 1000000000 }

#define SYSFS_REMOTE_GLOB   "/sys/module/*wacom/drivers/*/*/wacom_remote/*/remote_mode"


static void fixup_remotes()
{
	glob_t results;

	glob(SYSFS_REMOTE_GLOB, GLOB_NOSORT, NULL, &results);

	if (results.gl_pathc > 0) {
		char **ppath;

		for (ppath = results.gl_pathv; ppath && *ppath; ppath++) {
			char *path = *ppath;		
			struct stat st;

			if (stat(path, &st) == 0 && !(st.st_mode & S_IROTH)) {
				if (chmod(path, st.st_mode | S_IRGRP | S_IROTH)) {
					int len = strlen(path) + 100;
					char err[len];

					snprintf(err, sizeof(err), "Unable to update permission for '%s'", path);
					perror(err);
				}
				else {
					printf("Permissions updated for '%s'\n", path);
				}
			}
		}
	}

	globfree(&results);
}

static void mainloop(long timer_ns)
{
	struct timespec t = NSEC_TO_TIMESPEC(timer_ns);

	while (1) {
		fixup_remotes();
		nanosleep(&t, NULL);
	}
}

static void help(char *name)
{
	fprintf(stderr, "Usage: %s [hz]\n", name);
	fprintf(stderr, "Update ExpressKey Remote mode switch permissions.\n");
	fprintf(stderr, "\n");
	fprintf(stderr, "  hz            Polling rate for new devices in Hz (default %d)\n", HZ_DEFAULT);
	fprintf(stderr, "\n");
}

int main(int argc, char *argv[])
{
	int hz;

	if (argc == 1) {
		hz = HZ_DEFAULT;
	}
	else if (argc == 2) {
		hz = atoi(argv[1]);
		if (hz < HZ_LOWER || hz > HZ_UPPER) {
			fprintf(stderr, "Invalid hz value. Must be between %d and %d.\n", HZ_LOWER, HZ_UPPER);
			fprintf(stderr, "\n");
			help(argv[0]);
			return 1;
		}
	}
	else {
		help(argv[0]);
		return 1;
	}

	if (geteuid() != 0) {
		fprintf(stderr, "Program not running as root. May not be able to fix permissions!\n");
	}

	mainloop(HZ_TO_NSEC(hz));

	return 0;
}