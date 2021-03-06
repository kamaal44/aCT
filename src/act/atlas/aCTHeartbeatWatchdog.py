# Tool for updating heartbeats when the main process has failed.
from act.common.aCTLogger import aCTLogger
from act.arc.aCTDBArc import aCTDBArc
from act.atlas.aCTDBPanda import aCTDBPanda
from act.atlas.aCTPanda import aCTPanda
import sys
import time

def main():
    if len(sys.argv) != 2:
        print("Usage: python aCTHeartbeatWatchdog.py timelimit")
        sys.exit(1)

    timelimit = int(sys.argv[1])

    # logger
    logger = aCTLogger('aCTHeartbeatWatchdog')
    log = logger()
    # database
    dbarc = aCTDBArc(log)
    dbpanda = aCTDBPanda(log)

    # Query for running jobs with theartbeat longer than timelimit seconds ago
    select = "sendhb=1 and " \
             "pandastatus in ('sent', 'starting', 'running', 'transferring') and " \
             "theartbeat != 0 and " + dbpanda.timeStampLessThan("theartbeat", timelimit)
    columns = ['pandaid', 'pandastatus', 'proxyid', 'sitename', 'theartbeat']
    jobs = dbpanda.getJobs(select, columns)

    if jobs:
        print('Found %d jobs with outdated heartbeat (older than %d seconds):\n' % (len(jobs), timelimit))
        print('\t'.join(['pandaid', 'site', 'status', 'theartbeat', 'Panda response']))

        # Panda server for each proxy
        pandas = {}
        for job in jobs:
            proxyid = job['proxyid']
            if proxyid not in pandas:
                panda = aCTPanda(log, dbarc.getProxyPath(proxyid))
                pandas[proxyid] = panda

            response = pandas[proxyid].updateStatus(job['pandaid'], job['pandastatus'])
            print('\t'.join([str(job['pandaid']), job['sitename'], job['pandastatus'], str(job['theartbeat']), str(response)]))
            # update heartbeat time in the DB
            dbpanda.updateJob(job['pandaid'], {'theartbeat': dbpanda.getTimeStamp(time.time()+1)})


if __name__ == '__main__':
    main()
