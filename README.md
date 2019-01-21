# eld-2018
공유를 위한 eld 모듈입니다.

mulrel-nel: Multi-relational Named Entity Linking
========

A Python implementation of Multi-relatonal Named Entity Linking described in 

[1] Phong Le and Ivan Titov (2018). [Improving Entity Linking by 
Modeling Latent Relations between Mentions](https://arxiv.org/pdf/1804.10637.pdf). ACL 2018.

Written and maintained by Phong Le (ple [at] exseed.ed.ac.uk )

#### Train

To train a 3-relation ment-norm model, from the main folder run 

    export PYTHONPATH=$PYTHONPATH:../
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
