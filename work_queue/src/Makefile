include ../../config.mk
include ../../rules.mk

# Note that this list of sources only contains
# the items that go into libwork_queue.a, to
# avoid polluting user programs with our internal code.

SOURCES_LIBRARY = \
	batch_job.c \
	batch_job_chirp.c \
	batch_job_cluster.c \
	batch_job_condor.c \
	batch_job_local.c \
	batch_job_work_queue.c \
	work_queue.c \
	work_queue_catalog.c \
	work_queue_resources.c

SOURCES_WORKER = \
	work_queue_process.o \
	work_queue_watcher.o

PUBLIC_HEADERS = batch_job.h work_queue.h

LIBDTTOOLS = ${CCTOOLS_HOME}/dttools/src/libdttools.a
LIBCHIRP = $(CCTOOLS_HOME)/chirp/src/libchirp.a
EXTERNALS = $(LIBDTTOOLS) $(LIBCHIRP)

EXTERNAL_DEPENDENCIES = ../../chirp/src/libchirp.a ../../dttools/src/libdttools.a
LIBRARIES = libwork_queue.a
OBJECTS = $(OBJECTS_LIBRARY) $(OBJECTS_WORKER) work_queue_test_main.o
OBJECTS_LIBRARY = $(SOURCES_LIBRARY:%.c=%.o)
OBJECTS_WORKER = $(SOURCES_WORKER:%.c=%.o)
PROGRAMS = work_queue_worker work_queue_status work_queue_example work_queue_pool
PUBLIC_HEADERS = batch_job.h work_queue.h
SCRIPTS = work_queue_submit_common condor_submit_workers sge_submit_workers torque_submit_workers pbs_submit_workers ec2_submit_workers ec2_remove_workers slurm_submit_workers work_queue_graph_log
TEST_PROGRAMS = work_queue_example work_queue_test work_queue_test_watch work_queue_priority_test
TARGETS = $(LIBRARIES) $(PROGRAMS) $(TEST_PROGRAMS) bindings

all: $(TARGETS)

libwork_queue.a: $(OBJECTS_LIBRARY)
work_queue_test work_queue_test_watch: work_queue_test_main.o
work_queue_worker: $(OBJECTS_WORKER)
$(PROGRAMS) $(TEST_PROGRAMS) $(CCTOOLS_SWIG_BINDINGS): libwork_queue.a $(EXTERNAL_DEPENDENCIES)

bindings: $(CCTOOLS_SWIG_BINDINGS)
$(CCTOOLS_SWIG_BINDINGS): libwork_queue.a work_queue.i
	@$(MAKE) -C $@

CCTOOLS_SWIG_BINDINGS_INSTALL = $(CCTOOLS_SWIG_BINDINGS:%=install-%)
install-bindings: $(CCTOOLS_SWIG_BINDINGS_INSTALL)
$(CCTOOLS_SWIG_BINDINGS_INSTALL): $(CCTOOLS_SWIG_BINDINGS)
	@$(MAKE) -C $(@:install-%=%) install

CCTOOLS_SWIG_BINDINGS_CLEAN = $(CCTOOLS_SWIG_BINDINGS:%=clean-%)
clean-bindings: $(CCTOOLS_SWIG_BINDINGS_CLEAN)
$(CCTOOLS_SWIG_BINDINGS_CLEAN):
	@$(MAKE) -C $(@:clean-%=%) clean

install: all install-bindings
	mkdir -p $(CCTOOLS_INSTALL_DIR)/bin
	chmod 755 $(SCRIPTS)
	cp $(PROGRAMS) $(SCRIPTS) $(CCTOOLS_INSTALL_DIR)/bin/
	mkdir -p $(CCTOOLS_INSTALL_DIR)/lib
	cp $(LIBRARIES) $(CCTOOLS_INSTALL_DIR)/lib/
	mkdir -p $(CCTOOLS_INSTALL_DIR)/doc
	cp work_queue_example.c $(CCTOOLS_INSTALL_DIR)/doc/
	mkdir -p $(CCTOOLS_INSTALL_DIR)/include/cctools
	cp $(PUBLIC_HEADERS) $(CCTOOLS_INSTALL_DIR)/include/cctools/

clean: clean-bindings
	rm -rf $(OBJECTS) $(LIBRARIES) $(PROGRAMS) $(TEST_PROGRAMS)

test: all

.PHONY: all clean install test $(CCTOOLS_SWIG_BINDINGS) bindings $(CCTOOLS_SWIG_BINDINGS_INSTALL) install-bindings $(CCTOOLS_SWIG_BINDINGS_CLEAN) clean-bindings
