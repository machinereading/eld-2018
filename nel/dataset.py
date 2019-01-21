import re
import time
import pickle

wiki_link_prefix = 'http://en.wikipedia.org/wiki/'


def read_csv_file(path):
    data = {}
    with open(path, 'r', encoding='utf8') as f:
        for line in f:
            comps = line.strip().split('\t')
            doc_name = comps[0] + ' ' + comps[1]
            mention = comps[2]
            lctx = comps[3]
            rctx = comps[4]

            if comps[6] != 'EMPTYCAND':
                cands = [c.split(',') for c in comps[6:-2]]
                cands = [(','.join(c[2:]).replace('"', '%22').replace(' ', '_'), float(c[1])) for c in cands]
            else:
                cands = []

            gold = comps[-1].split(',')
            if gold[0] == '-1':
                gold = (','.join(gold[2:]).replace('"', '%22').replace(' ', '_'), 1e-5, -1)
            else:
                gold = (','.join(gold[3:]).replace('"', '%22').replace(' ', '_'), 1e-5, -1)

            if doc_name not in data:
                data[doc_name] = []
            data[doc_name].append({'mention': mention,
                                   'context': (lctx, rctx),
                                   'candidates': cands,
                                   'gold': gold})

    return data


def read_conll_file(data, path):
    conll = {}
    with open(path, 'r', encoding='utf8') as f:
        cur_sent = None
        cur_doc = None

        for line in f:
            line = line.strip()
            if line.startswith('-DOCSTART-'):
                docname = line.split()[1][1:]
                conll[docname] = {'sentences': [], 'mentions': []}
                cur_doc = conll[docname]
                cur_sent = []

            else:
                if line == '':
                    cur_doc['sentences'].append(cur_sent)
                    cur_sent = []

                else:
                    comps = line.split('\t')
                    tok = comps[0]
                    cur_sent.append(tok)

                    if len(comps) >=6 :
                        bi = comps[1]
                        wikilink = comps[4]
                        if bi == 'I':
                            cur_doc['mentions'][-1]['end'] += 1
                        else:
                            new_ment = {'sent_id': len(cur_doc['sentences']),
                                        'start': len(cur_sent) - 1,
                                        'end': len(cur_sent),
                                        'wikilink': wikilink}
                            cur_doc['mentions'].append(new_ment)

    # merge with data
    rmpunc = re.compile('[^a-zA-Z0-9ㄱ-ㅣ가-힣]+')
    removed_mentions = 0
    no_entity_docs = []
    for doc_name, content in data.items():
        conll_doc = conll[doc_name.split()[0]]
        content[0]['conll_doc'] = conll_doc
        cur_conll_m_id = 0
        conll_m_id_buf = 0
        errorus_mentions = []
        for m in content:
            mention = m['mention']
            gold = m['gold']

            while True:
                try:
                    cur_conll_m = conll_doc['mentions'][cur_conll_m_id]
                except IndexError:
                    errorus_mentions.append(m)
                    cur_conll_m_id = conll_m_id_buf
                    break
                cur_conll_mention = ' '.join(conll_doc['sentences'][cur_conll_m['sent_id']][cur_conll_m['start']:cur_conll_m['end']])
                # if doc_name.split()[0] == "현대_(기업)":
                #     print(rmpunc.sub('', cur_conll_mention.lower()) , '|',  rmpunc.sub('', mention.lower()))
                if rmpunc.sub('', cur_conll_mention.lower()) == rmpunc.sub('', mention.lower()):
                    m['conll_m'] = cur_conll_m
                    conll_m_id_buf = cur_conll_m_id
                    cur_conll_m_id += 1
                    break
                else:
                    cur_conll_m_id += 1

        content = list(filter(lambda x: x not in errorus_mentions, content))
        removed_mentions += len(errorus_mentions)
        data[doc_name] = content
        if len(content) == 0:
            no_entity_docs.append(doc_name)

    print("%d mentions removed" % removed_mentions)
    print("%d docs removce" % len(no_entity_docs))
    data = {k: v for k, v in data.items() if k not in no_entity_docs}

    return data


# def read_PPRforNED(data, path):
#     pat = re.compile('^[0-9]+')
#     rmpunc = re.compile('[\W]+')
#     for doc_name, content in data.items():
#         m = pat.match(doc_name)
#         if m is None:
#             raise Exception('doc_id not found in ' + doc_name)
#         doc_id = doc_name[m.start():m.end()]
#
#         # read PPRforNED file
#         new_content = []
#         with open(path + '/' + doc_id, 'r', encoding='utf8') as f:
#             m = None
#
#             for line in f:
#                 comps = line.strip().split('\t')
#                 if comps[0] == 'ENTITY':
#                     entity = comps[-1][4:].replace('"', '%22').replace(' ', '_')
#
#                     if entity == 'NIL':
#                         continue
#                     else:
#                         m = {}
#                         new_content.append(m)
#                         m['mention'] = comps[7][9:]
#
#                 elif comps[0] == 'CANDIDATE' and m is not None:
#                     cand = comps[5][len('url:' + wiki_link_prefix):].replace('"', '%22').replace(' ', '_')
#                     if 'candidates' not in m:
#                         m['candidates'] = []
#                     m['candidates'].append((cand, 1e-5))
#
#         i = 0
#         j = 0
#         while i < len(content) and j < len(new_content):
#             mi = content[i]
#             mj = new_content[j]
#             if rmpunc.sub('', mi['mention'].lower()) == rmpunc.sub('', mj['mention'].lower()):
#                 mi['PPRforNED_candidates'] = []
#                 cand_p = {c[0]:c[1] for c in m['candidates']}
#                 for cand, _ in mj['candidates']:
#                     mi['PPRforNED_candidates'].append((cand, cand_p.get(cand, 1e-3)))
#                 i += 1
#                 j += 1
#             else:
#                 j += 1


def load_person_names(path):
    data = []
    with open(path, 'r', encoding='utf8') as f:
        for line in f:
            data.append(line.strip().replace(' ', '_'))
    return set(data)


def find_coref(ment, mentlist, person_names):
    cur_m = ment['mention'].lower()
    coref = []
    for m in mentlist:
        if len(m['candidates']) == 0 or m['candidates'][0][0] not in person_names:
            continue

        mention = m['mention'].lower()
        start_pos = mention.find(cur_m)
        if start_pos == -1 or mention == cur_m:
            continue

        end_pos = start_pos + len(cur_m) - 1
        if (start_pos == 0 or mention[start_pos-1] == ' ') and \
                (end_pos == len(mention) - 1 or mention[end_pos + 1] == ' '):
            coref.append(m)

    return coref


def with_coref(dataset, person_names):
    for data_name, content in dataset.items():
        for cur_m in content:
            coref = find_coref(cur_m, content, person_names)
            if coref is not None and len(coref) > 0:
                cur_cands = {}
                for m in coref:
                    for c, p in m['candidates']:
                        cur_cands[c] = cur_cands.get(c, 0) + p
                for c in cur_cands.keys():
                    cur_cands[c] /= len(coref)
                cur_m['candidates'] = sorted(list(cur_cands.items()), key=lambda x: x[1])[::-1]


def eval(testset, system_pred):
    gold = []
    pred = []

    for doc_name, content in testset.items():
        gold += [c['gold'][0] for c in content]
        pred += [c['pred'][0] for c in system_pred[doc_name]]

    true_pos = 0
    for g, p, in zip(gold, pred):
        if g == p and p != 'NIL':
            true_pos += 1

    precision = true_pos / len([p for p in pred if p != 'NIL'])
    recall = true_pos / len(gold)
    print(precision)
    print(recall)
    f1 = 2 * precision * recall / (precision + recall)
    return f1


def eval_to_log(testset, system_pred):
    gold = []
    pred = []
    mention = []
    cand_length = []

    for doc_name, content in testset.items():
        cand_length += [len(c['candidates']) for c in content]
        mention += [c['mention'] for c in content]
        gold += [c['gold'][0] for c in content]
        pred += [c['pred'][0] for c in system_pred[doc_name]]

    true_pos = 0
    true_pos_2 = 0
    pred_num = 0
    gold_num = 0
    with open('./test_result_marking.txt', 'w', encoding='utf-8') as f:
        f.write('ment' + '\t' + 'gold' + '\t' + 'pred' + '\t' + 'cand_length' + '\n')
        for m, g, p, l in zip(mention, gold, pred, cand_length):
            if l > 1:
                gold_num += 1
                if p != 'NIL':
                    pred_num += 1
            if g == p and p != 'NIL':
                true_pos += 1
                if l > 1:
                    true_pos_2 += 1                 
            line = m + '\t' + g + '\t' + p + '\t' + str(l) + '\n'
            f.write(line)

    precision = true_pos / len([p for p in pred if p != 'NIL'])
    recall = true_pos / len(gold)
    precision2 = true_pos_2 / pred_num
    recall2 = true_pos_2 / gold_num
    print(precision)
    print(recall)
    f1 = 2 * precision * recall / (precision + recall)
    f1_2 = 2 * precision2 * recall2 / (precision2 + recall2)
    print("==========================")
    print(precision2)
    print(recall2)
    print(f1_2)
    return "evaluation finished"


def eval_for_api(testset, system_pred):
    gold = []
    pred = []
    score = []
    confidence = []
    mention = []
    cand_length = []

    true_pos = 0
    true_pos_2 = 0
    pred_num = 0
    gold_num = 0
    print(system_pred)
    with open('./test_result_marking.txt', 'w', encoding='utf-8') as f:
        f.write('ment' + '\t' + 'gold' + '\t' + 'pred' + '\t' + 'cand_length' + '\n')
        for doc_name, content in testset.items():
            f.write(doc_name.split()[0]+"\n")
            cand_length += [len(c['candidates']) for c in content]
            mention += [c['mention'] for c in content]
            gold += [c['gold'][0] for c in content]
            pred += [c['pred'][0] for c in system_pred[doc_name]]
            score += [c['score'] for c in system_pred[doc_name]]
            confidence += [c['confidence'] for c in system_pred[doc_name]]
            for m, g, p, s, c, l in zip(mention, gold, pred, score, confidence, cand_length):
                if l > 1:
                    gold_num += 1
                    if p != 'NIL':
                        pred_num += 1
                if g == p and p != 'NIL':
                    true_pos += 1
                    if l > 1:
                        true_pos_2 += 1                 
                line = m + '\t' + g + '\t' + p + '\t' + str(s) + '\t' + str(c) + '\t' + str(l) + '\n'
                f.write(line)

    # precision = true_pos / len([p for p in pred if p != 'NIL'])
    # recall = true_pos / len(gold)
    # precision2 = true_pos_2 / pred_num
    # recall2 = true_pos_2 / gold_num
    # print(precision)
    # print(recall)
    # f1 = 2 * precision * recall / (precision + recall)
    # f1_2 = 2 * precision2 * recall2 / (precision2 + recall2)
    # print("==========================")
    # print(precision2)
    # print(recall2)
    # print(f1_2)
    return "evaluation finished"


class CoNLLDataset:
    """
    reading dataset from CoNLL dataset, extracted by https://github.com/dalab/deep-ed/
    """

    def __init__(self, path, person_path):
        print('load csv')
        self.train = read_csv_file(path + '/cs_train.tsv')
        self.test = read_csv_file(path + '/cs_test.tsv')
        self.dev = read_csv_file(path + '/cs_dev.tsv')
        
        print('process coref')
        person_names = load_person_names(person_path)
        with_coref(self.train, person_names)
        with_coref(self.test, person_names)
        with_coref(self.dev, person_names)

        print('load conll')
        read_conll_file(self.train, path + '/cs_train.conll')
        read_conll_file(self.test, path + '/cs_test.conll')
        read_conll_file(self.dev, path + '/cs_dev.conll')


class EvalDataset:

    def __init__(self, path, person_path):
        print('load csv')
        self.test = read_csv_file(path + '/cs_test.tsv')
        self.dev = read_csv_file(path + '/cs_dev.tsv')
        
        print('process coref')
        person_names = load_person_names(person_path)
        with_coref(self.test, person_names)
        with_coref(self.dev, person_names)

        print('load conll')
        read_conll_file(self.test, path + '/cs_test.conll')
        read_conll_file(self.dev, path + '/cs_dev.conll')


class TestDataset:

    def __init__(self, path, person_path):
        print('load csv')
        self.tta = read_csv_file(path + '/tta.tsv')
        
        print('process coref')
        person_names = load_person_names(person_path)
        with_coref(self.tta, person_names)

        print('load conll')
        read_conll_file(self.tta, path + '/tta.conll')


if __name__ == "__main__":
    path = '../data/generated/test_train_data/'
    person_path = '../data/basic_data/p_e_m_data/persons.txt'

    dataset = CoNLLDataset(path, person_path)

    # for doc_name, content in train_dataset.items():
    #     print(doc_name)
    #     for c in content:
    #         print(c)
    #         time.sleep(2)
    #     time.sleep(5)
    # from pprint import pprint
    # pprint(dataset.ace2004, width=200)

