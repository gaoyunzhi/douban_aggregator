import os
import sys

def kill():
	os.system("ps aux | grep ython | grep douban | awk '{print $2}' | xargs kill -9")

def setup():
	kill()
	if 'kill' in str(sys.argv):
		return 
	print(str(sys.argv))
	print(sys.argv)
	if 'debug' in str(sys.argv):
		os.system('python3 douban.py')
	elif 'skip' in str(sys.argv):
		os.system('nohup python3 douban.py skip &')
	else:
		os.system('nohup python3 douban.py &')


if __name__ == '__main__':
	setup()