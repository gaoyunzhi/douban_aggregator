import os
import sys

def kill():
	os.system("ps aux | grep ython | grep douban | awk '{print $2}' | xargs kill -9")

def setup():
	kill()
	if 'kill' in str(sys.argv):
		return 
	addtional_arg = ' '.join(sys.argv[1:])
	command = 'python3 douban.py %s' % addtional_arg
	if 'debug' in str(sys.argv):
		os.system(command)
	else:
		os.system('nohup %s &' % command)

if __name__ == '__main__':
	setup()