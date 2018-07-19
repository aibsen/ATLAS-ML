import optparse 
import os

def main():
	parser = optparse.OptionParser(" -p <path to files>")
	parser.add_option("-p", dest="path", type="string", \
                      help="specify file listing examples")
	(options, args) = parser.parse_args()
	path=options.path


	with open(path+'/good.txt', 'a') as good:
		for file in os.listdir(path+'/2'):
    			good.write(file+'\n')

	with open(path+'/bad.txt', 'a') as bad:
		for file in os.listdir(path+'/0'):
			bad.write(file+'\n')

if __name__=='__main__':
	main()
