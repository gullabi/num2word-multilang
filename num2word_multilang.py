import sys
import os
import re
import inflect
import yaml
import json
import argparse

class Normalizer(object):
    def __init__(self,filename,outname=None,language='ca',step_cache=False):
        if not os.path.isfile(filename):
            raise IOError("%s not found"%filename)
        self.filename = filename
        self.language = language
        if not outname:
            self.outfile = filename[:-4]+'_norm.txt'
        else:
            self.outfile = outname
        self.step_cache = step_cache
        self.logfile = 'num2word.log'
        self.p = inflect.engine()
        self.transdict_fname = 'translation_dict.yaml'

        self.sphinx_struct = re.compile('^(.+)( \(.+\)$)')
        #self.digits = re.compile('(?<!\w)\d+(?!\w)')
        self.digits = re.compile('\d+(?!\w)')

        self.number_digits = re.compile('(?<=\d)\.(?=\d)')
        self.number_commas = re.compile('(?<=\d),(?=\d)')
        self.number_space = re.compile('(?<=\d) (?=\d)')
        self.number_slash = re.compile('(?<=\d)/(?=\d)')
        self.trailing_dash = re.compile('((?<=\d)– )|( –(?=\d))')
        self.number_dash = re.compile('(?<=\d)(-|–)(?=\d)')

        self.commas = re.compile(',')

        if os.path.isfile(self.transdict_fname):
            print('loading translations from cache...')
            self.translation_dict = yaml.load(open(self.transdict_fname))
        else:
            print('no cache found.')
            self.translation_dict = {}

    def process(self, sphinx=False):
        with open(self.outfile,'w') as out,\
             open(self.logfile,'w') as log:
            count = 0
            for line in open(self.filename,'r').readlines():
                count += 1
                if self.step_cache:
                    if count%150000 == 0:
                        print(count)
                        self.write_out_dict()
                if sphinx:
                    match = self.sphinx_struct.search(line)
                    if not match:
                        pline, f_id = line, ''
                    else:
                        pline, f_id = match.groups()
                else:
                    pline = line
                try:
                    new_line = self.normalize_translate(pline)
                    new_line = self.normalize_translate(new_line, inword=True)
                except Exception as e:
                    print(e)
                    print(line)
                    self.write_out_dict()
                    #sys.exit()
                    new_line = line
                if sphinx:
                    new_line = new_line + f_id + '\n'
                out.write(new_line)
                if new_line.strip() != pline.strip():
                    log.write(line)
                    log.write(new_line)

    def normalize_translate(self,text, inword=False):
        d_text = self.digit_normalize(text)
        normalized=False
        starts_with_number=False
        for number in self.digits.findall(d_text):
            if d_text.find(number) == 0:
                starts_with_number = True
            normalized_num = self.transcribe_translate(number)
            if not inword:
                # replace only the first occurence, since the number
                # could be a part of a larger digit further in the string
                #d_text = d_text.replace(number,normalized_num,1)
                d_text = re.sub('((?<=(\s|\'))|^){0}(?=(\s|,|\.))'.format(number),normalized_num,d_text)
            else:
                # if number comes after a word or dash replace it with space
                # plus the written form
                d_text = re.sub('(?<=\w)(-|){0}(?=(\s|,|\.))'.format(number),' '+normalized_num,d_text)
            normalized=True
        if normalized:
            if starts_with_number:
                # Assuming that all the lines start with capitals, we 
                # use the capitalized number text
                d_text=d_text[0].upper()+d_text[1:]
        return d_text

    def digit_normalize(self,text):
        d_text = self.number_digits.sub('',text)
        d_text = self.number_space.sub('',d_text)
        d_text = self.number_commas.sub(' coma ',d_text)
        d_text = self.trailing_dash.sub(' ',d_text)
        d_text = self.number_slash.sub(' ',d_text)
        d_text = self.number_dash.sub(' ',d_text)
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
        trans = trans.replace("-un", "-u")
        return self.commas.sub('',trans).lower()

    def write_out_dict(self):
        with open(self.transdict_fname,'w') as out:
            yaml.dump(self.translation_dict,out)

    def process_parlament_json(self):
        '''
        for processing the results of the parlament-scrape in json format
        '''
        interventions = json.load(open(self.filename))
        count = 0
        for int_code, intervention in interventions.items():
            for text_inter in intervention['text']:
                count += 1
                if self.step_cache:
                    if count%1000 == 0:
                        print(count)
                        self.write_out_dict()
                try:
                    new_text = self.normalize_translate(text_inter[1])
                except Exception as e:
                    print(e)
                    print(line)
                    self.write_out_dict()
                    #sys.exit()
                    new_text = text
                text_inter[1] = new_text

        with open(self.outfile,'w') as out:
            json.dump(interventions, out, indent=4)

    def process_parlament_mongo(self):
        '''
        for processing the results of the parlament-scrape in json format
        '''
        new_lines = []
        for line in open(self.filename).readlines():
            intervention = json.loads(line.strip())
            count = 0
            for text_inter in intervention['value']['text']:
                count += 1
                if self.step_cache:
                    if count%1000 == 0:
                        print(count)
                        self.write_out_dict()
                try:
                    new_text = self.normalize_translate(text_inter[1])
                except Exception as e:
                    print(e)
                    print(line)
                    self.write_out_dict()
                    #sys.exit()
                    new_text = text
                text_inter[1] = new_text
            new_lines.append(intervention)

        with open(self.outfile,'w') as out:
            #json.dump(new_lines, out)
            pass

        with open(self.outfile,'w') as out:
            for line in new_lines:
                out.write('%s\n'%json.dumps(line))

def main():
    usage = 'usage: %(prog)s -i -o [options]'
    parser = argparse.ArgumentParser(description='number normalizer',\
                                     usage=usage)
    processes = ['text', 'parlament', 'sphinx', 'mongo']
    parser.add_argument("-i","--in", dest="filename", default=None,\
                        help="input file", type=str)
    parser.add_argument("-o", "--out", dest="outname", default=None,\
                        help="output file", type=str)
    parser.add_argument("-p", "--process", dest="process", default="text",\
                        help="specific process for input file, could be %s"\
                        %str(processes))
    args = parser.parse_args()

    if not args.filename or not args.outname:
        parser.print_usage()
        raise ValueError('Input or output path is missing')

    if args.process not in processes:
        msg = 'process needs to be %s'%str(processes)
        raise ValueError(msg)

    if not os.path.isfile(args.filename):
        raise IOError("%s not found"%filename)

    norm = Normalizer(args.filename, args.outname,'ca')
    if args.process == 'parlament':
        norm.process_parlament_json()
    elif args.process == 'mongo':
        norm.process_parlament_mongo()
    elif args.process == 'sphinx':
        norm.process(sphinx=True)
    else:
        norm.process()
    norm.write_out_dict()

if __name__ == "__main__":
    main()
