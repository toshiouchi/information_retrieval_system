<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <title>規程検索システム</title>
    <link rel="icon" href="S-favicon.ico">
</head>

<body>

<?php

ini_set('display_errors', "Off");

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
    #echo "socket_connect() failed.\n";
    echo "検索サーバーが準備中です。10分ほどたってから検索しなおしてみてください。\n";
    exit;
}

// ソケット通信の処理...

// 検索分をサーバーに送信
socket_write($socket, $data, strlen($data));

//サーバーからの検索結果を受け取る。
$response = socket_read($socket, 8192);

// 表示する。
echo "<table border='1px'>\n";

echo $response;

echo "</table>\n検索終了\n</div>";

// ソケットをクローズ
socket_close($socket);
?>

</body>
</html>
