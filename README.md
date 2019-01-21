# eld-2018
공유를 위한 eld 모듈입니다.

## Introduction

<https://github.com/lephong/mulrel-nel> 의 모델을 기반으로 작업한 모델입니다.

### Environment

virtual or conda environment with python 3.6 is recommended

execute `pip3 install -r requirements.txt`

#### Train

For train, you have to make data files(cs_train.conll, cs_train.tsv) with the same format of test or dev files in the same directory.
To train a 3-relation ment-norm model, from the main folder run 

    python -u -m nel.main --mode train --n_rels 3 --mulrel_type ment-norm
 
Using a GTX 1080 Ti GPU it will take about 1 hour. The output is a model saved in two files: 
`model.config` and `model.state_dict` . 

#### Evaluation

Execute

    python -u -m nel.main --mode eval
    
#### Test for plain text

Execute

    python -u -m nel.main --mode test --input_file [FILENAME]

It shows the result of entity linking for `FILENAME`
Input file should contain each input document per one line.
Input file template is shown in test_text.txt

#### To use ETRI Module

After installing ETRI Module, change `host` and `port` at nel/etri.py, line 11 and 12.