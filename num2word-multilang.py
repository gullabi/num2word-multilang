import sys
import os
import re
import inflect

class Normalizer(object):
    def __init__(self,filename,outname=None,language='ca'):
        if not os.path.isfile(filename):
            raise IOError("%s not found"%filename)
        self.filename = filename
        self.language = language
        if not outname:
            self.outfile = filename[:-4]+'_norm.txt'
        else:
            self.outfile = outname
        self.logfile = 'num2word.log'
        self.p = inflect.engine()
        self.translation_dict = {}

    def process(self):
        with open(self.outfile,'w') as out,\
             open(self.logfile,'w') as log:
            for line in open(self.filename,'r').readlines():
                new_line = self.normalize_translate(line)
                out.write(new_line)
                if new_line != line:
                    log.write(line)
                    log.write(new_line)

    def normalize_translate(self,text):
        d_text = self.digit_normalize(text)
        normalized=False
        starts_with_number=False
        for number in re.findall('\d+',d_text):
            if d_text.find(number) == 0:
                starts_with_number = True
            normalized_num = self.transcribe_translate(number)
            # replace only the first occurence, since the number
            # could be a part of a larger digit further in the string
            d_text = d_text.replace(number,normalized_num,1)
            normalized=True
        if normalized:
            if starts_with_number:
                # Assuming that all the lines start with capitals, we 
                # use the capitalized number text
                d_text=d_text[0].upper()+d_text[1:]
        return d_text

    def digit_normalize(self,text):
        number_digits = '(?<=\d)\.(?=\d)'
        number_commas = '(?<=\d),(?=\d)'
        d_text = re.sub(number_digits,'',text)
        d_text = re.sub(number_commas,' coma ',d_text)
        return d_text

    def transcribe_translate(self,number):
        word_en = self.p.number_to_words(number,andword='')
        if self.translation_dict.get(word_en):
            word_target_lang = self.translation_dict.get(word_en)
        else:
            word_target_lang = self.translate(word_en)
            self.translation_dict[word_en] = word_target_lang
        return word_target_lang

    def translate(self,word_en):
        trans = os.popen('echo %s | apertium en-ca'%word_en).read().strip()
        return re.sub(',','',trans).lower()

def main():
    if len(sys.argv) < 2:
        print('Arguments missing.\n'\
              'Usage: %s <in-file> <out-file> <lang>'%__file__)
        print('Currently lang defaults to catalan.')
        sys.exit()
    if len(sys.argv) > 2:
        outname = sys.argv[2]
    else:
        outname = None
    filename = sys.argv[1]
    if not os.path.isfile(filename):
        raise IOError("%s not found"%filename)

    norm = Normalizer(filename,outname,'ca')
    norm.process()

if __name__ == "__main__":
    main()
