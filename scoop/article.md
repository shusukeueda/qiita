Qiita 初投稿です.

Python で気軽に並列 / 分散処理ができるシンプルなフレームワーク SCOOP というものを使ってみたので,
その使い方などのメモです.

Window のパッケージマネージャに Scoop というものがあるらしく同じ名前です.
いまのところ検索するとそちらばかりヒットしますね...

# SCOOP とは
Scalable COncurrent Operations in Python の略だそうです.

- [ドキュメント (英語)](https://scoop.readthedocs.io/en/0.7)

- [ソースコード (GitHub)](https://github.com/soravux/scoop)

現在バージョン 0.7.2 で開発中ですが,
ちょっとした計算を気軽に並列化 / 分散化できるので使い所は多そうです.

# 使い方
## インストール
pip でインストールできます.

```bash
$ pip3 install scoop
```

## 基本
基本的には, Python 標準の `map` 関数
(リストの要素それぞれに関数を適用する) を 
`scoop.futures.map` で置き換えることで並列化 / 分散化します.

たとえばリストの各要素を 2 乗するプログラムは

```python
data = range(12)

def func(num):
    return num ** 2

print(list(map(func, data)))
```

```:実行結果
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121]
```
と書けますが, これは各要素に対して独立に行えるので

```python
from scoop import futures

data = range(12)

def func(num):
    return num ** 2

if __name__ == "__main__":
    print(list(futures.map(func, data)))
```
とすることができます.
これだけで SCOOP が勝手に並列化 / 分散化してくれます.

注意点としては, **データと関数の定義はグローバルに,
SCOOP の処理は `if __name__ == "__main__":` 内に** 書くことが必要です.

グローバルの処理は各ノードでそれぞれ行われます.
すなわち, データと関数の定義は各ノードで共有されます.

一方, SCOOP の処理をグローバルに書いてしまうと各ノードで SCOOP が実行されバグります.

SCOOP の役割はタスクを各ノードに割り振ることなので,
マスターノードだけで実行するべきです.

そのためマスターノードで一度だけ実行されるよう `if __name__ == "__main__":` の中に書く必要があります.

## 実行
上のように SCOOP で書かれた Python スクリプトを実行するには

```bash
$ python3 -m scoop <ホスト情報> -n <プロセス数> <スクリプト名>
```
とします.

各ホスト (ノード) にはマスターノードからパスフレーズなしの鍵認証でログインできる必要があります.
ホスト情報はそのまま

```bash
--host <ホスト名> <ホスト名> ... <ホスト名>
```
とするか, あるいはホストファイルを

```
<ホスト名>
<ホスト名>
...
<ホスト名>
```
という形式で用意しておいて

```bash
--hostfile <ホストファイル名>
```
で指定することもできます.

指定したプロセス数はこれらのノードに適当に割り振られます.

たとえばホスト情報を何も指定しない場合はマスターノードにすべてのプロセスが割り振られ,
ノード数と同じ数のプロセス数を指定した場合はそれぞれ 1 プロセスずつ割り振られます.

それぞれのノードに割り振るプロセス数を指定したい場合は

```
<ホスト名> <プロセス数>
...
```
のように書くか, あるいはその数だけ同じホスト名を繰り返して書きます.

あとは指定した数を超えないように SCOOP がうまくやってくれます.

## ネットワーク
分散処理をする場合には,
上記のようにマスターノードから各スレーブノードにパスフレーズなしの鍵認証で SSH できる必要があります.

ホストファイルには IP アドレスまたは `~/.ssh/config` の接続名を書きます.
デフォルトのポート以外を使用する場合などは後者を使いましょう.

マスターノード自身は `127.0.0.1` を指定すればいいです.
以上のことを組み合わせて

```
127.0.0.1
172.17.0.3 2
slave2
slave3 3
```
のように書くこともできます.

## Docker を使う
実際に分散処理する段階では,
**すべてのノードで Python などの実行環境を一致させ,
また必要なスクリプトや読み込むファイルなども各ノードの同じ場所に置かれている必要があり** ます.

すこし面倒な作業ですが, Docker を使えば簡単に実現することができます.

Docker コンテナ上で実行するときには, SSH トンネルを使うように

```bash
$ python3 -m scoop --hostfile <ホストファイル名> -n <プロセス数> --tunnel <スクリプト名>
```
とオプションを指定します.
これを指定しないとうまく接続できず動かないので注意が必要です.

# サンプルコード
上の例で, ひとつの数字を 2 乗するのに 0.1 秒かかることにし,
マスターノードで実行時間をミリ秒単位で計ります.

```python:test.py
import time
import math

from scoop import futures

data = range(12)

def func(num):
    time.sleep(0.1)
    return num ** 2

if __name__ == "__main__":
    begin_time = time.time()

    res = list(futures.map(func, data))
    spent_time = math.ceil((time.time() - begin_time) * 1000)

    print(res)
    print("End at {} msec".format(spent_time))
```

```:hosts
127.0.0.1
172.17.0.3
172.17.0.4
```

直列に実行すると

```bash
$ python3 -m scoop -n 1 test.py
```

```bash:実行結果
[2019-08-30 18:24:09,805] launcher  INFO    SCOOP 0.7 1.1 on linux using Python 3.6.8 (default, Jan 14 2019, 11:02:34) [GCC 8.0.1 20180414 (experimental) [trunk revision 259383]], API: 1013
[2019-08-30 18:24:09,805] launcher  INFO    Deploying 1 worker(s) over 1 host(s).
[2019-08-30 18:24:09,805] launcher  INFO    Worker distribution: 
[2019-08-30 18:24:09,805] launcher  INFO       127.0.0.1:	0 + origin
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121]
End at 1233 msec
[2019-08-30 18:24:11,456] launcher  (127.0.0.1:41715) INFO    Root process is done.
[2019-08-30 18:24:11,457] launcher  (127.0.0.1:41715) INFO    Finished cleaning spawned subprocesses.
```
です.

プロセス数を 3 にしてみると

```bash
$ python3 -m scoop --hostfile hosts -n 3 --tunnel test.py
```

```bash:実行結果
[2019-08-30 18:19:56,455] launcher  INFO    SCOOP 0.7 1.1 on linux using Python 3.6.8 (default, Jan 14 2019, 11:02:34) [GCC 8.0.1 20180414 (experimental) [trunk revision 259383]], API: 1013
[2019-08-30 18:19:56,456] launcher  INFO    Deploying 3 worker(s) over 3 host(s).
[2019-08-30 18:19:56,456] launcher  INFO    Worker distribution: 
[2019-08-30 18:19:56,456] launcher  INFO       127.0.0.1:	0 + origin
[2019-08-30 18:19:56,456] launcher  INFO       172.17.0.3:	1 
[2019-08-30 18:19:56,456] launcher  INFO       172.17.0.4:	1 
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121]
End at 431 msec
[2019-08-30 18:19:57,828] launcher  (127.0.0.1:33243) INFO    Root process is done.
[2019-08-30 18:19:56,708] __main__  INFO    Worker(s) launched using /bin/bash
[2019-08-30 18:19:56,988] __main__  INFO    Worker(s) launched using /bin/bash
[2019-08-30 18:19:58,211] launcher  (127.0.0.1:33243) INFO    Finished cleaning spawned subprocesses.
```
と, 各ノードに 1 プロセスずつ割り振られ 3 分の 1 の計算時間になりました.

さらにプロセス数を 6 にしてみると

```bash
$ python3 -m scoop --hostfile hosts -n 6 --tunnel test.py
```

```bash:実行結果
[2019-08-30 18:21:21,617] launcher  INFO    SCOOP 0.7 1.1 on linux using Python 3.6.8 (default, Jan 14 2019, 11:02:34) [GCC 8.0.1 20180414 (experimental) [trunk revision 259383]], API: 1013
[2019-08-30 18:21:21,617] launcher  INFO    Deploying 6 worker(s) over 3 host(s).
[2019-08-30 18:21:21,617] launcher  INFO    Worker distribution: 
[2019-08-30 18:21:21,617] launcher  INFO       127.0.0.1:	1 + origin
[2019-08-30 18:21:21,617] launcher  INFO       172.17.0.3:	2 
[2019-08-30 18:21:21,617] launcher  INFO       172.17.0.4:	2 
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121]
End at 214 msec
[2019-08-30 18:21:22,748] launcher  (127.0.0.1:45215) INFO    Root process is done.
[2019-08-30 18:21:21,862] __main__  INFO    Worker(s) launched using /bin/bash
[2019-08-30 18:21:22,094] __main__  INFO    Worker(s) launched using /bin/bash
[2019-08-30 18:21:23,100] launcher  (127.0.0.1:45215) INFO    Finished cleaning spawned subprocesses.
```
と各ノードのプロセス数が 2 になり,
計算時間がさらに半分になったことが確認できます.

# まとめ
以上のように簡単に並列 / 分散処理をすることができます.

細かいチューニングなどはできませんが,
すこし重い計算をするときなどに気軽に触ってみてはいかがでしょうか.

興味を持たれた方はぜひ [公式ドキュメント](https://scoop.readthedocs.io/en/0.7) も参照してみてください.

各ノードで環境や必要なファイルを同一にしなければいけないのは注意です.
Docker を使いましょう.
