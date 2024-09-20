import random
import time
import threading
import os
import socket
from sentence_transformers import SentenceTransformer, util
from simpleneighbors import SimpleNeighbors
import datetime
import sys
import signal
import spacy
#from unstructured.partition.pdf import partition_pdf
#from unstructured.partition.html import partition_html
#import requests
import urllib.request
#import fitz
import pymupdf as fitz
import time

# PDF をテキスト化したファイル名　ファイルはカレントディレクトリに corpus フォルダを作ってそこに置く。

def main():
    
    # ファイルの定義
    URL0 = []
    docname = []
    URL0.append( "/pdf1.pdf" )
    docname.append('PDF1のドキュメント名')
    URL0.append( "/pdf2.pdf" )
    docname.append('PDF2のドキュメント名')
    URL0.append( "/pdf3.pdf" )
    docname.append('PDF3のドキュメント名')
    URL0.append( "/pdf4.pdf" )
    docname.append('PDF4のドキュメント名' )
    URL0.append( "/pdf5.pdf" )
    docname.append('PDF5のドキュメント名')

    # PDF ファイルの DL と テキストファイルへの変換
    pdf = []
    filename = []
    URL = []
    for pdf_name in URL0:
        pdf_name1 = pdf_name.split( "/" )[-1]
        pdf.append( pdf_name1 )
        filename.append( pdf_name1.replace( ".pdf", ".txt ") )
        URL.append( "http://www.example.com" + pdf_name )

    for URL0, pdfname, fname in zip(URL, pdf, filename ):
        #urlData = requests.get(URL0).content
        with urllib.request.urlopen(URL0) as u:
            with open( "corpus/" + pdfname ,mode='wb') as f:
                f.write(u.read())
        #pdf_html = partition_html( url = URL0 )
        #pdf_elements = partition_pdf("corpus/" + pdfname )

        # Initialize an empty string to store extracted text
        extracted_text = ""    
    
        pdf_document = "corpus/" + pdfname
        doc = fitz.open(pdf_document)
    
        # Iterate through each page and extract text
        for page_num in range(doc.page_count):
            page = doc[page_num]
            extracted_text += page.get_text()
    
        # Close the PDF document
        doc.close()
    
        with open( "corpus/" + fname, mode='w', encoding = "UTF-8" ) as f:
            f.write( extracted_text )
        
    # この検索システムは、文章単位で検索を行います。検索システムに読み込ませるテキストファイルのフォーマットは、
    # 検索されてほしいと予想される文章ごとに改行することが必要です。逆に文章の途中で改行していない方が良いです。
    # PDF をテキスト化したファイルについては、改訂履歴、目次、附則、施工日、改正日などを削除すると良いと思います。
    # filename + "_2.txt" ファイルを作るためには、このセルのプログラムか前のセルのプログラムが役に立つかもしれません。
    # このプログラムは、python の自然言語ライブラリー spacy の日本語モジュール ja_ginza を使って、文章ごとに改行するプログラムです。
    # 完全ではありません。できありは、 filename + "_2.txt" というファイル名です。必ず、確認、修正をお願いいたします。
    # _2.txt ファイルにおていは、文章の途中で改行されているところが残っていないか確認するなどです。

    # テキストファイルを一行が文章になるように修正。
    file_orig = []
    nlp = spacy.load('ja_ginza')

    for l, file in enumerate( filename ):
        #print( "file:", file )
        # テキストファイルを read で開く。
        f = open( "corpus/" + file, mode="r", encoding = "UTF-8")
        # *_2.txt を write で開く
        file_ori = "corpus/" + file.split(".")[0] + "_2.txt"
        file_orig.append( file_ori )
        fw = open( file_ori, mode="w", encoding = "UTF-8")

        # 最初の一行を読み込む
        line = f.readline()
        #print( "line0:", line )

        # 一つのドキュメントの全文をつなげる
        doc1 = ''
        while line:
            # PDF を書き出した時に <BR> が入ってしまうことがあるので削除。
            line = line.replace( "<BR>", "" )
            doc1 += line.replace( "\n", "").replace( "　", "").lstrip( ).rstrip()
            #doc1 += line.split()
            line = f.readline()
            #print( "file:", file, " line:", line)

        #print( "test2:")
        len1 = len( doc1 )
        #print( "len1:", len1 )
        doc2 = []
        #print( len1 > 1000)
        # nlp 関数があまり長い文章を受け付けないので、全文を 1000 文字程度で分ける。
        while True:
            if len( doc1 ) < 1000:
                #print( "ドキュメントの長さ:", len1 )
                tmp_doc = doc1[0:len1]
                #print( "    tmp_doc:", tmp_doc)
                doc2.append( tmp_doc )
                break
            else:
                #print( "ドキュメントの長さ:", len1 )
                pos = doc1.find( "。", 1000 )
                if pos == -1:
                    pos = doc1.find( " ", 1000 )
                    if pos == -1:
                        pos = doc1.find( "\n", 1000 )
                tmp_doc = doc1[0:pos + 1]
                if tmp_doc == "" or tmp_doc == "\n":
                    #print( "pos:", pos)
                    #print( "doc1:", doc1 )
                	#print( "tmp_doc:", tmp_doc)
                	break
                #print( "tmp_doc:", tmp_doc)
                doc2.append( tmp_doc )
                doc1 = doc1[pos + 1:]
                #print( "    doc1:", doc1 )
                len1 = len( doc1 )
                #break
    
        #print( "test3")
    
        # 1000文字程度に区切られた文を、nlp 関数で一文章ごとに区切る。
        for doc3 in doc2:    
            doc = nlp(doc3)
            for sent in doc.sents:
                sent = str( sent )
                last_sent = ''
                if len( sent ) < 10:
                    sentence = last_sent + sent
                    last_sent = sentence
                    #print(sentence  ) 
                else:
                    last_sent = sent
                    sentence = sent
                    #print( sentence )
                    fw.write( sentence + "\n" )
                #print( "last_sent:", last_sent)
            
        f.close()
        fw.close()
        #print("\n")
        #print( docname[l] + "完了。" )
        #分かりやすいように改行。
        #print("\n\n\n")
        #input()

    
    #print( "ドキュメントの処理が完了しました。念のため *_2.txt ファイルを、目視でフォーマットがくずれてないか確認してください。")

    # filename + "_2.txt"　という全ファイルの一行一行を、一行が、「docname + "<sep>"  + 文章」に整形して 
    # output_file に書き出す。output_file を検索システムが読み込む。


    #複数のファイルを一つの corpus/inf_sec.txt ファイルにまとめる。
    output_file = "corpus/inf_sec.txt"

    f_write = open( output_file, 'w', encoding = "UTF-8" ) 
    for i, file in enumerate( file_orig ):
        f_origi = open( file, 'r', encoding = "UTF-8")
        line = f_origi.readline()
        while line:
            sentence = docname[i] + "<sep>" + line
            #print( sentence)
            f_write.write( sentence )
            line = f_origi.readline()
        f_origi.close()
    f_write.close()
    
if __name__ == '__main__':

    dt_now_jst_aware = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )

    while True:
        t_now = datetime.datetime.now().time()
        #print( t_now )
        if str( t_now )[:8] == '00:00:00':
            main()
            print( "robot was executed" )
            #break
        #time.sleep(0.95)
        
