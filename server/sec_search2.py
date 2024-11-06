from transformers import BertJapaneseTokenizer, BertModel
import random
import time
import os
import socket
from sentence_transformers import SentenceTransformer, util
from simpleneighbors import SimpleNeighbors
import datetime
import sys
#import fcntl
import signal
import time
import torch

class SentenceBertJapanese:
    def __init__(self, model_name_or_path, device=None):
        self.tokenizer = BertJapaneseTokenizer.from_pretrained(model_name_or_path)
        self.model = BertModel.from_pretrained(model_name_or_path)
        self.model.eval()

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.model.to(device)

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0] #First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    @torch.no_grad()
    def encode(self, sentences, batch_size=1):
        all_embeddings = []
        iterator = range(0, len(sentences), batch_size)
        for batch_idx in iterator:
            batch = sentences[batch_idx:batch_idx + batch_size]

            encoded_input = self.tokenizer.batch_encode_plus(batch, padding="longest", 
                                           truncation=True, return_tensors="pt").to(self.device)
            model_output = self.model(**encoded_input)
            sentence_embeddings = self._mean_pooling(model_output, encoded_input["attention_mask"]).to('cpu')

            all_embeddings.extend(sentence_embeddings)

        # return torch.stack(all_embeddings).numpy()
        return torch.stack(all_embeddings)



class SemanticSearch:
    #def __init__(self, model):
    def __init__(self):
        #self.encoder = SentenceTransformer(model["name"])
        #self.index = SimpleNeighbors(model["dims"], model["metric"])
        #if model["metric"] == "angular":
        #    self.metric_func = util.cos_sim
        #elif model["metric"] == "dot":
        #    self.metric_func = util.dot_score
        model = SentenceBertJapanese("sonoisa/sentence-bert-base-ja-mean-tokens-v2")
        self.encode = model.encode
        #self.encoder = SentenceTransformer(model["name"])
        #self.index = SimpleNeighbors(model["dims"], model["metric"])
        self.index = SimpleNeighbors( 768, "angular")
        #if model["metric"] == "angular":
        #    self.metric_func = util.cos_sim
        #elif model["metric"] == "dot":
        #    self.metric_func = util.dot_score
        self.metric_func = util.cos_sim

    def load_corpus(self, filename):
        with open(f"corpus/{filename}", encoding='UTF-8') as f:
            self.feed(f.read().split("\n"))

    #def feed(self, sentences):
    #    for sentence in sentences:
    #        tmp1 = sentence.split('<sep>')
    #        if len( tmp1 ) <= 1:
    #            break
    #        #print( tmp1 )
    #        sent = tmp1[1]
    #        vector = self.encoder.encode(sent)
    #        self.index.add_one(sentence, vector)
    #    self.index.build()
        
    def feed(self, sentences):
        for sentence in sentences:
            tmp1 = sentence.split('<sep>')
            if len( tmp1 ) <= 1:
                break
            #print( "tmp1:",tmp1 )
            sent = tmp1[1]
            #print( "sent:", sent )
            #vector = self.encoder.encode(sent)
            vector = self.encode([sent])
            vector = torch.squeeze( vector, dim = 0)
            #print( sentence )
            #print( vector )
            #print( "len of sentence:", len( sent ) )
            #print( "size of vector:", vector.size() )
            self.index.add_one(sentence, vector)
        self.index.build()
        

    #def find_nearest(self, query, n=20):
    #    vector = self.encoder.encode(query)
    #    nearests = self.index.nearest(vector, n)
    #    res = []
    #    for neighbor in nearests:
    #        dist = self.metric_func(vector, self.index.vec(neighbor))
    #        #res.append((neighbor, float(dist)))
    #        res.append( neighbor + "<sep>" + str(float(dist)))
    #    return res

    def find_nearest(self, query, n=20):
        #vector = self.encoder.encode(query)
        vector = self.encode([query])
        vector = torch.squeeze( vector )
        nearests = self.index.nearest(vector, n)
        res = []
        for neighbor in nearests:
            dist = self.metric_func(vector, self.index.vec(neighbor))
            #res.append((neighbor, float(dist)))
            res.append( neighbor + "<sep>" + str(float(dist)))
        return res

if __name__ == "__main__":

    URL = {}

    f = open( "corpus/doc_url.txt", mode = "r", encoding="UTF-8" )
    
    line = f.readline()
    
    while line:
       #print( "line:", line )
       line_split = line.split( "'" )
       #print( "line_split[1]:", line_split[1] )
       #print( "line_split[3]:", line_split[3] )
       URL[line_split[1]] = line_split[3]
       line = f.readline()
       
    f.close()

    #exit()

    # モデルを定義する。
    #model = find_model_with_name(
    #    models, "multi-qa-mpnet-base-cos-v1")
        
    # SemantciSearch インスタンスを定義する。
    #ss = SemanticSearch(model)
    ss = SemanticSearch()
    # 検索対象のテキストファイルを読み込む。
    ss.load_corpus('inf_sec.txt')
    #ss.load_corpus('inf_sec3.txt')

    dt_now_jst_aware = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )

    # テキストファイル読み込みに時間がかかるので、読み込み終わったら表示する。
    print( "start" )

    # ソケットのパラメーター定義
    #server_ip = "127.0.0.1"
    server_ip = "192.168.13.250"
    server_port = 10000
    listen_num = 10
    buffer_size = 8192

    # 1.ソケットオブジェクトの作成
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #tcp_server.setblocking(0)

    # 2.作成したソケットオブジェクトにIPアドレスとポートを紐づける
    tcp_server.bind((server_ip, server_port))
    tcp_server.settimeout( 1.0 )

    # 3.作成したオブジェクトを接続可能状態にする
    tcp_server.listen(listen_num)
    #tcp_server.setblocking(0)
    #tcp_server.settimeout(0)

    # 4.ループして接続を待ち続ける
    f = open( "search_sec.log", mode = "a", encoding="UTF-8" )
    while True:
        try:
            # 5.クライアントと接続する
            client,address = tcp_server.accept()
            # 6.データを受信する
            data = client.recv(buffer_size)
            data = data.decode('UTF-8')
            print("[*] Received Data : {}\n".format(data)) # data は検索文。
            data_split = data.split( '<sep>' )

            #検索実行
            res = ss.find_nearest(data_split[0])
            
            dt_now = datetime.datetime.now()
            str_log = str( dt_now ) + "\t" + data_split[1] + "\t" + data_split[0] + "\n"
            print( "str_log", str_log )
            f.write( str_log )
            f.flush()
        
            send_result = ""
        
            #検索結果20個のループ
            for i, r in enumerate( res ):
                result = str( r )
                res_split = result.split( "<sep>" )
                send_result += "<tr>"
                send_result += "<td width ='300px'><a href='" + URL[res_split[0]] + "'>" + res_split[0] + "</a></td>"
                send_result += "<td width='900px'>" + res_split[1] + "</td>"
                send_result += "<td width = '60px'>" + res_split[2][:5] + "</td>"
                send_result += "</tr>\n"

            print( "send_result:", send_result )
            print( " len ", len( send_result ) )

            client.send( send_result.encode( "UTF-8" ) )

            # 8.接続を終了させる
            client.close()

        except socket.timeout as e:
            #exceptLog( e )
            #print("timeout")
            t_now = datetime.datetime.now().time()
            #print( t_now )
            if '00:30:0' ==  str( t_now )[:7]:
                tcp_server.close()
                
                # SemantciSearch インスタンスを定義する。
                #ss = SemanticSearch(model)
                ss = SemanticSearch()
                # 検索対象のテキストファイルを読み込む。
                print("reloading inf_sec.txt" )
                ss.load_corpus('inf_sec.txt')
                print("reloaded inf_sec.txt")
                
                # 1.ソケットオブジェクトの作成
                tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # 2.作成したソケットオブジェクトにIPアドレスとポートを紐づける
                tcp_server.bind((server_ip, server_port))
                tcp_server.settimeout( 1.0 )

                # 3.作成したオブジェクトを接続可能状態にする
                tcp_server.listen(listen_num)

                f1 = open( "corpus/doc_url.txt", mode = "r", encoding="UTF-8" )

                line = f1.readline()

                while line:
                    line_split = line.split( "'" )
                    URL[line_split[1]] = line_split[3]
                    line = f1.readline()
       
                f1.close()
