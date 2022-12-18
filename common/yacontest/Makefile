SHELL=/bin/bash -o pipefail

Q_MODE = @

# ---------------------------------------------------------------
# Make targets that are used by YandexContest

# Called at 'compile' stage
compile:
	$(Q_MODE) $(SHELL) ./run_build.sh

# Called at 'run' stage
run:
	$(Q_MODE) python3.7 ./runner.py --mode=yandex-contest
