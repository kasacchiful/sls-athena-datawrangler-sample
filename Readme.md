# AKIBA.AWS ONLINE 7 Sample Code

「AKIBA.AWS ONLINE 7」にて説明に使用したサンプルコードです。

## Requirement

- AWSアカウント
  - `AdministratorAccess` など、デプロイに必要な権限を割り当ててください
- AWS CLI v2
- node.js v14.x 以上
- python v3.8
- Docker
  - `sls deploy` 時にPythonパッケージビルドにDockerコンテナ使用してます
  - これは `serverless-python-requirements` プラグインで `dockerizePip: true` を指定しているためです

## Install

```bash
yarn install
```

## Deploy

### 1. AWS Data Wrangler Layer deploy

最初に「[AWS Data Wrangler](https://github.com/awslabs/aws-data-wrangler)」を
Lambda Layerにデプロイしておきます。

- [Release](https://github.com/awslabs/aws-data-wrangler/releases)ページから、
  Lambda Layer向けリリースパッケージをダウンロード
  - 今回のプロジェクトでLambdaはPython 3.8を使用するので、 `layer-<wranglerバージョン>-py3.8.zip` をダウンロードする

- 任意の名前のS3バケットをあらかじめ作成しておく
  - マネジメントコンソールまたはAWS CLIで作成してください
  - 例では `awswrangler-sample-lambdalayer` というバケット名を作成します。

- 作成したS3バケットに、Lambda Layer向けData Wranglerパッケージをアップロード

- `/cfn` にあるCloudFormationテンプレートをデプロイ
  - `awswrangler_layer.yml` 内にある `ContentUri` のS3 URIを適宜変更してください。

```bash
aws cloudformation deploy \
  --template-file ./cfn/awswrangler_layer.yml \
  --stack-name awswrangler-layer-deploy-stack \
  --capabilities CAPABILITY_IAM
```

- 作成したLambda LayerのARNを `serverless.yml` に書き換えてください。

```yaml
  wrangle:
    handler: functions/wrangle/index.handler
    role: AthenaLambdaRole
    memorySize: 512
    timeout: 900
    environment: ${self:custom.environment.${self:provider.stage}}
    layers:
      - "arn:aws:lambda:ap-northeast-1:000000000000:layer:awswrangler-layer-2_12_1-py3_8:1"  ## ここのARNを書き換える
    events:
      - httpApi:
          path: /wrangle
          method: get
```

### 2. Serverless deploy

- `serverless.yml` の冒頭のサービス名を適宜変更する
  - `awswrangler-sample` の部分はS3バケット名にも使っているので、適宜変更してS3バケットを一意の名前になるようにする

```yaml
service: awswrangler-sample
```

- Serverless Frameworkのデプロイをする

```bash
npx sls deploy
```

(AWSプロファイルを指定する場合):

```bash
npx sls deploy --aws-profile <プロファイル名>
```

デプロイが完了すると、エンドポイントが生成される。

```bash
endpoints:
  GET - https://XXXXXXXXXX.execute-api.ap-northeast-1.amazonaws.com/hello
  GET - https://XXXXXXXXXX.execute-api.ap-northeast-1.amazonaws.com/wrangle
```

### 3. Create and Upload Sample Data

サンプルデータを作成し、
デプロイで作成された `DataLakeBucket` にアップロードする。
(サービス名が `awswrangler-sample` の場合は、バケット名は `awswrangler-sample-datalake-bucket-dev` になる)

まず必要なPythonライブラリをPython仮想環境上にインストールする

```bash
cd data
python3 -m venv env
source env/bin/activate
pip install -U pip
pip install -r requirements.txt
```

`/data` にあるPythonファイルを実行する。
引数にバケット名を指定する。

```bash
python create_parquet_data.py "awswrangler-sample-datalake-bucket-dev"
```

(AWSプロファイルを指定する場合):

```bash
AWS_PROFILE=<プロファイル名> python create_parquet_data.py "awswrangler-sample-datalake-bucket-dev"
```

データ生成後は、仮想環境を終了してプロジェクトトップディレクトリに移動する。

```bash
deactivate
cd ..
```

## Execute

デプロイ時に表示された API Gateway の URL を CURL で実行

```bash
## Data Wrangler不使用
curl "https://XXXXXXXXXX.execute-api.ap-northeast-1.amazonaws.com/hello"
```

```bash
## Data Wrangler使用
curl "https://XXXXXXXXXX.execute-api.ap-northeast-1.amazonaws.com/wrangle"
```

## Remove

- `DataLakeBucket` 及び `AthenaResultBucket` を空にする

```bash
aws s3 rm s3://awswrangler-sample-datalake-bucket-dev --recursive
aws s3 rm s3://awswrangler-sample-athena-result-bucket-dev --recursive
```

- Serverless Frameworkでデプロイしたプロジェクトを削除

```bash
npx sls remove
```

(AWSプロファイルを指定する場合):

```bash
npx sls remove --aws-profile <プロファイル名>
```

なお、AthenaのWorkGroupが削除できない場合は、
以下のコマンドを実行してAthena WorkGroupを削除、及び
`AthenaResultBucket` を空にしてから、再度 `npx sls remove` を実行すると良い。
(Athenaワークグループ名は `<Serverless Framework サービス名>-athena-workgroup-dev` になる)

```bash
aws s3 rm s3://awswrangler-sample-athena-result-bucket-dev --recursive
aws athena delete-work-group --work-group awswrangler-sample-athena-workgroup-dev --recursive-delete-option
npx sls remove
```

これでもダメなら、マネジメントコンソールから残っているリソースを手動削除して、
CloudFormationのデプロイスタックを削除する。

- Lambda Layerのスタックを削除

```bash
aws cloudformation delete-stack \
  --stack-name awswrangler-layer-deploy-stack
```

- Data Wranglerパッケージ削除 & Lambda Layer用バケット削除

```bash
aws s3 rm s3://awswrangler-sample-lambdalayer --recursive
aws s3 rb s3://awswrangler-sample-lambdalayer
```
