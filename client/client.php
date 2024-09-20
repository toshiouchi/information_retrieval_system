<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <title>セキュリティ</title>
    <link rel="icon" href="S-favicon.ico">
</head>

<body>

<?php

// html から 検索文を受け取る
$query = $_GET['query'];

$client = $_SERVER['REMOTE_ADDR'];

$data = $query . "<sep>" . $client;

// 検索文を表示する
echo "<div align='center'>検索文：$query<br /><br />\n";
ob_flush();
flush();

// ソケット作成
$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);

// サーバに接続
$address = '127.0.0.1';
$port = 10000;
$result = socket_connect($socket, $address, $port);

if ($result === false) {
    echo "socket_connect() failed.\n";
    exit;
}

// ソケット通信の処理...

// メッセージを送信
socket_write($socket, $data, strlen($data));

$URL = array( 
       "個人情報保護方針" => "/security/kojinjyouhou_hogohohari.pdf",
       "情報セキュリティポリシー" => "/syanaikitei/pdf/sec_policy.pdf",
       "機密保持規程" => "/syanaikitei/pdf/5-1.pdf",
       "情報セキュリティ管理規程" => "/syanaikitei/pdf/jyouhousekanrikitei.pdf",
       "情報セキュリティ運用マニュアル" => "/syanaikitei/pdf/seq-manual_v22.pdf",
       "情報保護物理的安全措置マニュアル" => "/security/anzen.pdf",
       "ネットワーク管理マニュアル" => "/security/network_kanri.pdf",
       "ウィルス対策マニュアル" => "/security/virus.pdf",
       "ネチケットマニュアル" => "/security/netiket.pdf",
       "個人情報管理規程" => "/syanaikitei/pdf/5-5.pdf",
       "個人情報管理マニュアル" => "/security/kojin.pdf",
       "個人情報保護運用マニュアル" => "/security/unyou.pdf",
       "苦情要望対応マニュアル " => "/security/kuzyou.pdf",
       "特定個人情報取扱規程" => "/syanaikitei/pdf/tokuteikojinjyouhou.pdf"
        );


// サーバからの応答を受け取る
$n = 0;
while(true){
    $response = socket_read($socket, 1024);
    if ( strncmp( $response, 'end', strlen( "end" ) ) == 0 ){
        break;
    }
    
    // ドキュメント名を取得する。
    $res_split = explode( "<sep>", $response );
    
    // ドキュメント名、検索結果文章、確からしさの数値を array1 に格納する。
    $array1[$n][0] = $res_split[0];
    $array1[$n][1] = $res_split[1];
    $array1[$n][2] = substr( $res_split[2], 0, 5 );

    $n++;
    label1:
  }


// 表示する。
echo "<table border='1px'>\n";

for ($n=0; $n < count($array1); $n++) {
    echo "<tr><td width = '300px'><a href ='". $URL[$array1[$n][0]] . "'> ". $array1[$n][0] . "</a></td><td width='900px'>" . $array1[$n][1] . "</td><td>". $array1[$n][2] . "</td></tr>\n";
}

echo "</table>\n検索終了\n</div>";


// ソケットをクローズ
socket_close($socket);
?>

</body>
</html>