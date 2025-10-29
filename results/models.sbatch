#!/bin/bash
#
#SBATCH --job-name=dontcrash # Job name for tracking
#SBATCH --partition=tiger  	# Partition you wish to use (see above for list)
#SBATCH --cpus-per-task=128      # 128 cpu threads
#SBATCH --nodes=1
#SBATCH --mem=256000            # 256gigs of ram
#SBATCH --exclusive=mcs          # Exclusive mode, only this job will run
#SBATCH --time=2-00:00:00        # Job time limit set to 2 days (48 hours)
#
#SBATCH --mail-type=END,FAIL,TIME_LIMIT_80 # Events to send email on, remove if you don't want this
#SBATCH --output=joboutput_%j.out # Standard out from your job
#SBATCH --error=joboutput_%j.err  # Standard error from your job

## Initialisation ##
source /etc/profile.d/modules.sh
source /etc/profile.d/conda.sh

source ../venv/bin/activate
python independent_cascade.py -p 128 -o ICC-512 -t 512
python decreasing_cascade.py -p 128 -o DCC-512 -t 512
python linear_threshold.py -p 128 -o LTM-512 -t 512

