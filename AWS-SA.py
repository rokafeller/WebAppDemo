import json
import os
import sys
import requests
import time

#ELB_NAME='DFstack-SAelb-1Y0P309HF0NQ' #user input - from ELB name we can programmatically obtain all required information
ELB_NAME='DFstack-SAelb-TZZ9EUQ0RN0Q'

AWS='/Users/danferra/bin/aws '         #aws cli tool - needs to be properly installed & configured upfront
PROBEPAGE='/demo.html'                 #web page to reach

#Load information about our ELB, from which we obtain EC2 instance-id, from which we load all info about instance
elb = json.loads(os.popen(AWS+'elb describe-load-balancers --load-balancer-name '+ELB_NAME).read())['LoadBalancerDescriptions'][0]
inst_id=elb['Instances'][0]['InstanceId']
instance=json.loads(os.popen(AWS+'ec2 describe-instances --instance-id '+inst_id).read())['Reservations'][0]['Instances'][0]

print "Our instance: "+inst_id+', type: '+instance['InstanceType']+', ELB dns: '+elb['DNSName']
print 'Checking: http://'+elb['DNSName']+PROBEPAGE

try:
    probe = requests.get('http://'+elb['DNSName']+PROBEPAGE, timeout=1)
except requests.exceptions.RequestException:   
    print 'Status: not working'
    
    
    #Add inbound rule allow TCP:80 to WEB SG for inbound traffic to webserver EC2 instance
    print 'Adding inbound rule allow TCP:80 to webserver SG'
    cmd=AWS+'ec2 authorize-security-group-ingress --group-id '+instance['SecurityGroups'][0]['GroupId']+\
                                                ' --protocol tcp '+\
                                                 '--port 80 '+\
                                                 '--cidr 0.0.0.0/0'
    os.popen(cmd)
    
    #configure ELB health-check to probe on TCP:80 (can be more specific on /demo.html)
    print 'Configuring health check on TCP:80 on ELB '+elb['LoadBalancerName']
    cmd=AWS+'elb configure-health-check --load-balancer-name '+elb['LoadBalancerName']+\
                                      ' --health-check Target=TCP:80,'+\
                                                      'Interval=15,'+\
                                                      'UnhealthyThreshold=2,'+\
                                                      'HealthyThreshold=2,'+\
                                                      'Timeout=5'
    os.popen(cmd)
    
    #add EC2 webserver instance subnet to ELB 
    print "Adding instance subnet "+instance['SubnetId']+" to our ELB "+elb['LoadBalancerName']
    cmd=AWS+'elb attach-load-balancer-to-subnets '+\
             '--load-balancer-name '+elb['LoadBalancerName']+\
             ' --subnets '+instance['SubnetId']
    os.popen(cmd)
    
    
    #Add inbound rule allow TCP:80 to ELB SG to allow inbound traffic to ELB
    print 'Adding inbound rule allow TCP:80 to ELB SG'
    cmd=AWS+'ec2 authorize-security-group-ingress --group-id '+elb['SecurityGroups'][0]+\
                                                ' --protocol tcp '+\
                                                 '--port 80 '+\
                                                 '--cidr 0.0.0.0/0'
    os.popen(cmd)
    
    #Let's wait 5 seconds for commands to be properly delivered
    print 'Let\'s wait 5 seconds for commands to be properly delivered...'
    time.sleep(5)
    
    #Let's verify if this worked
    print 'Checking again: http://'+elb['DNSName']+PROBEPAGE
    try:
        probe = requests.get('http://'+elb['DNSName']+PROBEPAGE, timeout=1)
    except requests.exceptions.RequestException:   
        print 'Status: still not working, something went wrong.'
        sys.exit(0)
    print 'Status: working!'
    sys.exit(0)
     
print 'Status: working already.'
 
    
