import random
import time
import threading
import os
import socket
from sentence_transformers import SentenceTransformer, util
from simpleneighbors import SimpleNeighbors
import datetime
import sys
#import fcntl
import signal
import time

class SemanticSearch:
    def __init__(self, model):
        self.encoder = SentenceTransformer(model["name"])
        self.index = SimpleNeighbors(model["dims"], model["metric"])
        if model["metric"] == "angular":
            self.metric_func = util.cos_sim
        elif model["metric"] == "dot":
            self.metric_func = util.dot_score

    def load_corpus(self, filename):
        with open(f"corpus/{filename}", encoding='UTF-8') as f:
            self.feed(f.read().split("\n"))

    def feed(self, sentences):
        for sentence in sentences:
            tmp1 = sentence.split('<sep>')
            if len( tmp1 ) <= 1:
                break
            #print( tmp1 )
            sent = tmp1[1]
            vector = self.encoder.encode(sent)
            self.index.add_one(sentence, vector)
        self.index.build()

    def find_nearest(self, query, n=20):
        vector = self.encoder.encode(query)
        nearests = self.index.nearest(vector, n)
        res = []
        for neighbor in nearests:
            dist = self.metric_func(vector, self.index.vec(neighbor))
            #res.append((neighbor, float(dist)))
            res.append( neighbor + "<sep>" + str(float(dist)))
        return res

models = [
    {
        # Multi-lingual model of Universal Sentence Encoder for 15 languages:
        # Arabic, Chinese, Dutch, English, French, German, Italian, Korean, Polish, Portuguese, Russian, Spanish, Turkish.
        "name": "distiluse-base-multilingual-cased-v1",
        "dims": 512,
        "metric": "angular",
    },
    {
        # Multi-lingual model of Universal Sentence Encoder for 50 languages.
        "name": "distiluse-base-multilingual-cased-v2",
        "dims": 512,
        "metric": "angular",
    },
    {
        # Multi-lingual model of paraphrase-multilingual-MiniLM-L12-v2, extended to 50+ languages.
        "name": "paraphrase-multilingual-MiniLM-L12-v2",
        "dims": 384,
        "metric": "angular",
    },
    {
        # Multi-lingual model of paraphrase-mpnet-base-v2, extended to 50+ languages.
        "name": "paraphrase-multilingual-mpnet-base-v2",
        "dims": 768,
        "metric": "angular",
    },
    {
        # This model was tuned for semantic search:
        # Given a query/question, if can find relevant passages.
        # It was trained on a large and diverse set of (question, answer) pairs.
        # 215M (question, answer) pairs from diverse sources.
        "name": "multi-qa-mpnet-base-dot-v1",
        "dims": 768,
        "metric": "dot"
    },
    {
        # This model was tuned for semantic search:
        # Given a query/question, if can find relevant passages.
        # It was trained on a large and diverse set of (question, answer) pairs.
        # 215M (question, answer) pairs from diverse sources.
        "name": "multi-qa-mpnet-base-cos-v1",
        "dims": 768,
        "metric": "angular"
    },
]

def find_model_with_name(models, name):
    for model in models:
        if model["name"] == name:
            return model
    raise NameError(f"Could not find model {name}.")

def handler(signum,frame):
  # 何らかの処理
  f.close()
  sys.exit(0)


if __name__ == "__main__":

    # モデルを定義する。
    model = find_model_with_name(
        models, "multi-qa-mpnet-base-cos-v1")
        
    # SemantciSearch インスタンスを定義する。
    ss = SemanticSearch(model)
    # 検索対象のテキストファイルを読み込む。
    ss.load_corpus('inf_sec.txt')
    #ss.load_corpus('text3.txt')

    dt_now_jst_aware = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )

    # テキストファイル読み込みに時間がかかるので、読み込み終わったら表示する。
    print( "start" )

    # ソケットのパラメーター定義
    server_ip = "127.0.0.1"
    server_port = 10000
    listen_num = 10
    buffer_size = 1024

    # 1.ソケットオブジェクトの作成
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setblocking(0)

    # 2.作成したソケットオブジェクトにIPアドレスとポートを紐づける
    tcp_server.bind((server_ip, server_port))

    # 3.作成したオブジェクトを接続可能状態にする
    tcp_server.listen(listen_num)
    #tcp_server.setblocking(0)
    #tcp_server.settimeout(0)

    # 4.ループして接続を待ち続ける
    # log ファイルオープン
    f = open( "search_sec.log", mode = "a", encoding="UTF-8" )
    signal.signal(signal.SIGFPE, handler)
    while True:
        ## 5.クライアントと接続する
        #client,address = tcp_server.accept()
        #print("[*] Connected!! [ Source : {}]".format(address))
        
        
        client = None
        try:
            #clientsocket, (client_address, client_port) = tcp_server.accept()
            client,address = tcp_server.accept()
        except (BlockingIOError, socket.error):
            # まだソケットの準備が整っていない
            #continue
            pass

        #print('New client: {0}:{1}'.format(client_address, client_port))
        #print( " out of try except " )
        
        if client is not None: #クライアントから検索要求があったら。
            # 6.データを受信する
            print( "before recv" )
            data = client.recv(buffer_size)
            data = data.decode('UTF-8')
            print("[*] Received Data : {}\n".format(data)) # data は検索文。
            data_split = data.split( '<sep>' )
            #print( "data_split", data_split )
            print( "after recv" )

            #検索実行
            res = ss.find_nearest(data_split[0])
            dt_now = datetime.datetime.now()

            str_log = str( dt_now ) + "\t" + data_split[1] + "\t" + data_split[0] + "\n"
            print( "str_log", str_log )
            #fcntl.flock(f, fcntl.LOCK_EX)
            #f.write( "write test\n" )
            f.write( str_log )
            f.flush()
        
            #検索結果20個のループ
            for r in res:
                result = str( r )
                #print( result )
                # 検索結果をクライアントに返す。
                client.send( result.encode('UTF-8') )
                time.sleep( 0.01 )

            # 8.接続を終了させる
            str1 = "end"
            client.send( str1.encode("UTF-8") )
            print( "send end" )
            client.close()
            client = None
        
        #except (BlockingIOError,  socket.error):
        else: # クライアントから検索要求がない場合。
            t_now = datetime.datetime.now().time()
            #print( t_now )
            # 0時30分に、inf_sec.txt を読み込みなおす。
            if '00:30' ==  str( t_now )[:5]:
                # モデルを定義する。
                model = find_model_with_name(
                    models, "multi-qa-mpnet-base-cos-v1")
        
                # SemantciSearch インスタンスを定義する。
                ss = SemanticSearch(model)
                # 検索対象のテキストファイルを読み込む。
                ss.load_corpus('inf_sec.txt')
                print("reload inf_sec.txt")
                    #print( "now" )
                    #break
            #time.sleep(0.01)
        #except OSError:
        #    break
