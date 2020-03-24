import os
import urllib.request
import bz2
import time
import sys
import zipfile
from urllib.request import Request, urlopen
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

class Download:
    file = ''
    folder = './parsing/'
    
    def downloadstatus(self, count, block_size, total_size):
        # from https://blog.shichao.io/2012/10/04/progress_speed_indicator_for_urlretrieve_in_python.html
        global start_time
        if count == 0:
            start_time = time.time()
            return
        duration = time.time() - start_time
        progress_size = int(count * block_size)
        speed = int(progress_size / (1024 * duration))
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                        (percent, progress_size / (1024 * 1024), speed, duration))
        sys.stdout.flush()
        print("\n")
    
    def ifnotexist(self, url):
        self.file = self.folder + url.rsplit('/', 1)[-1]
        if not os.path.isfile(self.file):
            print('Downloading in ' + self.file)
            try:
                urllib.request.urlretrieve(url, self.file, self.downloadstatus)
            except Exception as inst:
                print(inst)
                print('  Encountered unknown error. Continuing.')
        else:
            print('File already downloaded ' + self.file)
        
        return self
    
    def bz2_decompress(self, file=''):
        if file == '':
            file = self.file
            
        extract_to = self.file.replace('.bz2','')
        if not os.path.isfile(extract_to):
            print('Decompressing to ' + extract_to)
            with open(extract_to, 'wb') as new_file, bz2.BZ2File(self.file, 'rb') as file:
                for data in iter(lambda : file.read(100 * 1024), b''):
                    new_file.write(data)
                
        return extract_to
    
    def zip_decompress(self, extract_to="", file=""):
        if file == '':
            file = self.file
            
        if not os.path.isdir(extract_to):
            print('Decompressing to ' + extract_to)
            with zipfile.ZipFile(self.file, "r") as zip_ref:
                zip_ref.extractall(extract_to)
                
        return extract_to
    
    def downloadpage(self, link):
        ua = UserAgent()
        
        response = Request(link, headers={'User-Agent': ua.random})
        return urlopen(response).read().decode('UTF-8').strip()
    
    def bp(self, raw_page):
        soup = BeautifulSoup(raw_page.content, 'html.parser')
        return soup
        