#!/usr/bin/env python3

import re
from pathlib import Path
from unidecode import unidecode
from utils import sanitize, line_rules, download
from concurrent.futures import ThreadPoolExecutor

download_me = download.Download()
validate_line = line_rules.LineRules()
clean_me = sanitize.Sanitization()

folder_dataset = download_me.ifnotexist('http://opus.nlpl.eu/download.php?f=OpenSubtitles/v2018/xml/it.zip').zip_decompress('./parsing')

def parsexmlfile(xml_path, count_file):
    mapping_normalization = [
      # If the sentence start with a number, the sentence is removed
      [ re.compile('^\d+(.*)'), u'' ],  
    
      # Remove the stuff inside ()[]{}
      [ re.compile('(\(|\[|{)[^(\)|\]|})]*(\)|\]|})'), u'' ],
      # must be twice time for nested parentheses
      [ re.compile('(\(|\[|{)[^(\)|\]|})]*(\)|\]|})'), u'' ],
     
      # remove uninteresting characters
      [ re.compile('\-|=|_|–|\+|\(|\||—|\)|\[|\]|~|\*|/|"|¨|\^'), u' ' ],     
      
      # Sanitize ... to .
      [ re.compile('\.+'), u'.' ],
      # normalize spaces
      [ re.compile('\n|\t|\r|\s+'), u' ' ],
    
      # accentate maiuscole
      [ re.compile('È'), u'e\'' ],
    
      # Sanitize single apex
      [ re.compile('´|`|\'\''), u'\'' ],
    
      # To avoid conflicts with single ' and accented letter we removed them
      [ re.compile('(\s|^)(\')([^\']*)(\')(\s|$)'), r'\3' ],
    
      # remove char for those cases
      [ re.compile('(#\d+)|#|(\s°)'), u'' ],
      
      # Sanitization for those cases
      [ u'n°' , u'numero ' ],  
    
      # Sanitization for currency values
      [ re.compile('\$\s*([0-9]+[.,]{0,1}[0-9]*)'), r'\1 dollari' ], 
      [ re.compile('([0-9]+[.,]{0,1}[0-9]*)\s*\$'), r'\1 dollari' ],
      [ re.compile('(₤|£)\s*([0-9]+[.,]{0,1}[0-9]*)'), r'\2 lire' ], 
      [ re.compile('([0-9]+[.,]{0,1}[0-9]*)\s*₤'), r'\1 lire' ],
      [ re.compile('(€)\s*([0-9]+[.,]{0,1}[0-9]*)'), r'\2 euro' ], 
      [ re.compile('([0-9]+[.,]{0,1}[0-9]*)\s*€'), r'\1 euro' ],
      [ u'¢' , u'c' ],  
    
      # space trim - it must be reapplied again
      [ re.compile('\s+'), u' ' ]
    ]
    
    mapping_normalization_after_decode = [
      # Convert old fashion accented letter to the real accented letter
      [ u'E\' ', u'è ' ],
      [ re.compile('a\'(\s|$|,|\.|\?)'), r'à\1' ], 
      [ re.compile('e\'(\s|$|,|\.|\?)'), r'è\1' ],
      [ re.compile('i\'(\s|$|,|\.|\?)'), r'ì\1' ],
      [ re.compile('o\'(\s|$|,|\.|\?)'), r'ò\1' ],
      [ re.compile('u\'(\s|$|,|\.|\?)'), r'ù\1' ],     
    ] 
    
    fp = open(xml_path,encoding='utf-8')
    result = open( './output/opensubtitles_' + count_file + '.txt', 'w' )
    
    text = fp.read()
    text = clean_me.maybe_normalize(text, mapping_normalization, False)
    
    # Opensubtiles Dataset contains no-ASCII char
    #  we use unidecode to delegate all unicode char processing
    #  to keep all vowels properly accented, and at the same time eliminate the other unicode characters, 
    #  you need to use a substitution with place holders
    text = text.replace('à', '<PH_A>')
    text = text.replace('è', '<PH_E>')
    text = text.replace('ì', '<PH_I>')
    text = text.replace('ò', '<PH_O>')
    text = text.replace('ù', '<PH_U>')
    text = unidecode(text)
    text = text.replace('<PH_A>','à')
    text = text.replace('<PH_E>','è')
    text = text.replace('<PH_I>','ì')
    text = text.replace('<PH_O>','ò')
    text = text.replace('<PH_U>','ù')
    text = clean_me.maybe_normalize(text, mapping_normalization_after_decode, False)
      
    for line in text.splitlines():
      line = clean_me.cleansingleline(line).strip()
      if len(line) <= 2:
          continue
       
      if validate_line.startswith(line, ['<']):
          continue
       
      if validate_line.contain(line, ['®', '{', '}', '©', '±', '_', '@', '+']):
          continue
        
      text += line + "\n"
    
    result.write(text)
    result.close()

start_year=1920
pathlist = Path(folder_dataset).glob('**/*.xml')

print('  Parsing in progress')
count_file = 0

# Parse 5 files at once
pool = ThreadPoolExecutor(max_workers=5)

for xml_path in pathlist:
  year_folder = str(xml_path.parent.parent._parts[len(xml_path.parent.parent._parts)-1])
  year_folder_int = int(year_folder)
  if(year_folder_int<start_year):
      continue

  xml_path = str(xml_path)
  pool.submit(parsexmlfile, xml_path, count_file)
#  parsexmlfile(xml_path, count_file)

  count_file +=1

pool.shutdown(wait=True)