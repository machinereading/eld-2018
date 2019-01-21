# eld-2018
공유를 위한 eld 모듈입니다.

## Introduction

<https://github.com/lephong/mulrel-nel> 의 모델을 기반으로 작업한 모델입니다.

### Environment

virtual or conda environment with python 3.6 is recommended

#### Train

To train a 3-relation ment-norm model, from the main folder run 

    python -u -m nel.main --mode train --n_rels 3 --mulrel_type ment-norm
 
Using a GTX 1080 Ti GPU it will take about 1 hour. The output is a model saved in two files: 
`model.config` and `model.state_dict` . 

#### Evaluation

Execute

    python -u -m nel.main --mode eval
    
#### Test for plain text

Execute

    python -u -m nel.main --mode text

It shows the result of entity linking for test_text.txt
