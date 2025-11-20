"""
Comprehensive AWS Service URL Mappings
Generated from boto3.Session().get_available_services()
"""

# Comprehensive mapping of AWS services to their console URLs
COMPREHENSIVE_AWS_SERVICE_URLS = {
    # Analytics
    'athena': 'https://{region}.console.aws.amazon.com/athena/home?region={region}',
    'emr': 'https://{region}.console.aws.amazon.com/emr/home?region={region}',
    'redshift': 'https://{region}.console.aws.amazon.com/redshiftv2/home?region={region}',
    'quicksight': 'https://{region}.quicksight.aws.amazon.com/sn/start',
    'glue': 'https://{region}.console.aws.amazon.com/glue/home?region={region}',
    'kinesis': 'https://{region}.console.aws.amazon.com/kinesis/home?region={region}',
    'kinesis-analytics': 'https://{region}.console.aws.amazon.com/kinesisanalytics/home?region={region}',
    'kinesis-firehose': 'https://{region}.console.aws.amazon.com/firehose/home?region={region}',
    'data-pipeline': 'https://{region}.console.aws.amazon.com/datapipeline/home?region={region}',
    
    # Compute
    'ec2': 'https://{region}.console.aws.amazon.com/ec2/home?region={region}',
    'lambda': 'https://{region}.console.aws.amazon.com/lambda/home?region={region}',
    'batch': 'https://{region}.console.aws.amazon.com/batch/home?region={region}',
    'elastic-beanstalk': 'https://{region}.console.aws.amazon.com/elasticbeanstalk/home?region={region}',
    'lightsail': 'https://lightsail.aws.amazon.com/ls/webapp/home/instances',
    'ecs': 'https://{region}.console.aws.amazon.com/ecs/home?region={region}',
    'eks': 'https://{region}.console.aws.amazon.com/eks/home?region={region}',
    'fargate': 'https://{region}.console.aws.amazon.com/ecs/home?region={region}#/clusters',
    
    # Storage
    's3': 'https://s3.console.aws.amazon.com/s3/home?region={region}',
    'efs': 'https://{region}.console.aws.amazon.com/efs/home?region={region}',
    'fsx': 'https://{region}.console.aws.amazon.com/fsx/home?region={region}',
    'glacier': 'https://{region}.console.aws.amazon.com/glacier/home?region={region}',
    'storage-gateway': 'https://{region}.console.aws.amazon.com/storagegateway/home?region={region}',
    'backup': 'https://{region}.console.aws.amazon.com/backup/home?region={region}',
    
    # Database
    'rds': 'https://{region}.console.aws.amazon.com/rds/home?region={region}',
    'dynamodb': 'https://{region}.console.aws.amazon.com/dynamodbv2/home?region={region}',
    'elasticache': 'https://{region}.console.aws.amazon.com/elasticache/home?region={region}',
    'neptune': 'https://{region}.console.aws.amazon.com/neptune/home?region={region}',
    'documentdb': 'https://{region}.console.aws.amazon.com/docdb/home?region={region}',
    'keyspaces': 'https://{region}.console.aws.amazon.com/keyspaces/home?region={region}',
    'timestream': 'https://{region}.console.aws.amazon.com/timestream/home?region={region}',
    
    # Networking
    'vpc': 'https://{region}.console.aws.amazon.com/vpc/home?region={region}',
    'cloudfront': 'https://console.aws.amazon.com/cloudfront/home',
    'route53': 'https://console.aws.amazon.com/route53/home',
    'api-gateway': 'https://{region}.console.aws.amazon.com/apigateway/home?region={region}',
    'apigateway': 'https://{region}.console.aws.amazon.com/apigateway/home?region={region}',
    'direct-connect': 'https://{region}.console.aws.amazon.com/directconnect/v2/home?region={region}',
    'app-mesh': 'https://{region}.console.aws.amazon.com/appmesh/home?region={region}',
    'cloud-map': 'https://{region}.console.aws.amazon.com/cloudmap/home?region={region}',
    'global-accelerator': 'https://console.aws.amazon.com/globalaccelerator/home',
    
    # Security & Identity
    'iam': 'https://console.aws.amazon.com/iam/home',
    'cognito': 'https://{region}.console.aws.amazon.com/cognito/home?region={region}',
    'secrets-manager': 'https://{region}.console.aws.amazon.com/secretsmanager/home?region={region}',
    'secretsmanager': 'https://{region}.console.aws.amazon.com/secretsmanager/home?region={region}',
    'guardduty': 'https://{region}.console.aws.amazon.com/guardduty/home?region={region}',
    'inspector': 'https://{region}.console.aws.amazon.com/inspector/v2/home?region={region}',
    'macie': 'https://{region}.console.aws.amazon.com/macie/home?region={region}',
    'security-hub': 'https://{region}.console.aws.amazon.com/securityhub/home?region={region}',
    'waf': 'https://{region}.console.aws.amazon.com/wafv2/home?region={region}',
    'shield': 'https://console.aws.amazon.com/wafv2/shieldv2',
    'firewall-manager': 'https://{region}.console.aws.amazon.com/wafv2/fmsv2/home?region={region}',
    'certificate-manager': 'https://{region}.console.aws.amazon.com/acm/home?region={region}',
    'kms': 'https://{region}.console.aws.amazon.com/kms/home?region={region}',
    'cloudhsm': 'https://{region}.console.aws.amazon.com/cloudhsm/home?region={region}',
    'directory-service': 'https://{region}.console.aws.amazon.com/directoryservicev2/home?region={region}',
    'ram': 'https://{region}.console.aws.amazon.com/ram/home?region={region}',
    'sso': 'https://console.aws.amazon.com/singlesignon/home',
    
    # Management & Governance
    'cloudwatch': 'https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}',
    'cloudtrail': 'https://{region}.console.aws.amazon.com/cloudtrail/home?region={region}',
    'config': 'https://{region}.console.aws.amazon.com/config/home?region={region}',
    'cloudformation': 'https://{region}.console.aws.amazon.com/cloudformation/home?region={region}',
    'service-catalog': 'https://{region}.console.aws.amazon.com/servicecatalog/home?region={region}',
    'systems-manager': 'https://{region}.console.aws.amazon.com/systems-manager/home?region={region}',
    'ssm': 'https://{region}.console.aws.amazon.com/systems-manager/home?region={region}',
    'opsworks': 'https://{region}.console.aws.amazon.com/opsworks/home?region={region}',
    'trusted-advisor': 'https://console.aws.amazon.com/trustedadvisor/home',
    'personal-health-dashboard': 'https://phd.aws.amazon.com/phd/home',
    'managed-services': 'https://console.aws.amazon.com/managedservices/home',
    'control-tower': 'https://{region}.console.aws.amazon.com/controltower/home?region={region}',
    'license-manager': 'https://{region}.console.aws.amazon.com/license-manager/home?region={region}',
    'well-architected-tool': 'https://{region}.console.aws.amazon.com/wellarchitected/home?region={region}',
    'compute-optimizer': 'https://{region}.console.aws.amazon.com/compute-optimizer/home?region={region}',
    
    # Developer Tools
    'codecommit': 'https://{region}.console.aws.amazon.com/codesuite/codecommit/repositories?region={region}',
    'codebuild': 'https://{region}.console.aws.amazon.com/codesuite/codebuild/projects?region={region}',
    'codedeploy': 'https://{region}.console.aws.amazon.com/codesuite/codedeploy/applications?region={region}',
    'codepipeline': 'https://{region}.console.aws.amazon.com/codesuite/codepipeline/pipelines?region={region}',
    'codestar': 'https://{region}.console.aws.amazon.com/codesuite/codestar/home?region={region}',
    'cloud9': 'https://{region}.console.aws.amazon.com/cloud9/home?region={region}',
    'x-ray': 'https://{region}.console.aws.amazon.com/xray/home?region={region}',
    'codeartifact': 'https://{region}.console.aws.amazon.com/codesuite/codeartifact/repositories?region={region}',
    'codeguru': 'https://{region}.console.aws.amazon.com/codeguru/home?region={region}',
    
    # Machine Learning
    'sagemaker': 'https://{region}.console.aws.amazon.com/sagemaker/home?region={region}',
    'comprehend': 'https://{region}.console.aws.amazon.com/comprehend/home?region={region}',
    'lex': 'https://{region}.console.aws.amazon.com/lexv2/home?region={region}',
    'polly': 'https://{region}.console.aws.amazon.com/polly/home?region={region}',
    'rekognition': 'https://{region}.console.aws.amazon.com/rekognition/home?region={region}',
    'translate': 'https://{region}.console.aws.amazon.com/translate/home?region={region}',
    'transcribe': 'https://{region}.console.aws.amazon.com/transcribe/home?region={region}',
    'forecast': 'https://{region}.console.aws.amazon.com/forecast/home?region={region}',
    'personalize': 'https://{region}.console.aws.amazon.com/personalize/home?region={region}',
    'textract': 'https://{region}.console.aws.amazon.com/textract/home?region={region}',
    'kendra': 'https://{region}.console.aws.amazon.com/kendra/home?region={region}',
    'fraud-detector': 'https://{region}.console.aws.amazon.com/frauddetector/home?region={region}',
    'codeguru-reviewer': 'https://{region}.console.aws.amazon.com/codeguru/reviewer/home?region={region}',
    'lookout-for-vision': 'https://{region}.console.aws.amazon.com/lookoutvision/home?region={region}',
    'monitron': 'https://{region}.console.aws.amazon.com/monitron/home?region={region}',
    'lookout-for-metrics': 'https://{region}.console.aws.amazon.com/lookoutmetrics/home?region={region}',
    'lookout-for-equipment': 'https://{region}.console.aws.amazon.com/lookoutequipment/home?region={region}',
    'healthlake': 'https://{region}.console.aws.amazon.com/healthlake/home?region={region}',
    
    # Application Integration
    'sns': 'https://{region}.console.aws.amazon.com/sns/v3/home?region={region}',
    'sqs': 'https://{region}.console.aws.amazon.com/sqs/v2/home?region={region}',
    'step-functions': 'https://{region}.console.aws.amazon.com/states/home?region={region}',
    'mq': 'https://{region}.console.aws.amazon.com/amazon-mq/home?region={region}',
    'managed-workflows-for-apache-airflow': 'https://{region}.console.aws.amazon.com/mwaa/home?region={region}',
    'appflow': 'https://{region}.console.aws.amazon.com/appflow/home?region={region}',
    'eventbridge': 'https://{region}.console.aws.amazon.com/events/home?region={region}',
    
    # Business Applications
    'workmail': 'https://console.aws.amazon.com/workmail/home',
    'chime': 'https://chime.aws.amazon.com/',
    'workdocs': 'https://console.aws.amazon.com/zocalo/home',
    'alexa-for-business': 'https://{region}.console.aws.amazon.com/a4b/home?region={region}',
    'connect': 'https://{region}.console.aws.amazon.com/connect/home?region={region}',
    
    # End User Computing
    'workspaces': 'https://{region}.console.aws.amazon.com/workspaces/home?region={region}',
    'appstream': 'https://{region}.console.aws.amazon.com/appstream2/home?region={region}',
    'worklink': 'https://{region}.console.aws.amazon.com/worklink/home?region={region}',
    
    # IoT
    'iot-core': 'https://{region}.console.aws.amazon.com/iot/home?region={region}',
    'iot-greengrass': 'https://{region}.console.aws.amazon.com/iot/home?region={region}#/greengrasshub',
    'iot-analytics': 'https://{region}.console.aws.amazon.com/iotanalytics/home?region={region}',
    'iot-device-management': 'https://{region}.console.aws.amazon.com/iot/home?region={region}#/devicedefenderhub',
    'iot-events': 'https://{region}.console.aws.amazon.com/iotevents/home?region={region}',
    'iot-sitewise': 'https://{region}.console.aws.amazon.com/iotsitewise/home?region={region}',
    'iot-things-graph': 'https://{region}.console.aws.amazon.com/thingsgraph/home?region={region}',
    
    # Game Development
    'gamelift': 'https://{region}.console.aws.amazon.com/gamelift/home?region={region}',
    
    # Media Services
    'elemental-mediaconnect': 'https://{region}.console.aws.amazon.com/mediaconnect/home?region={region}',
    'elemental-mediaconvert': 'https://{region}.console.aws.amazon.com/mediaconvert/home?region={region}',
    'elemental-medialive': 'https://{region}.console.aws.amazon.com/medialive/home?region={region}',
    'elemental-mediapackage': 'https://{region}.console.aws.amazon.com/mediapackage/home?region={region}',
    'elemental-mediastore': 'https://{region}.console.aws.amazon.com/mediastore/home?region={region}',
    'elemental-mediatailor': 'https://{region}.console.aws.amazon.com/mediatailor/home?region={region}',
    'kinesis-video-streams': 'https://{region}.console.aws.amazon.com/kinesisvideo/home?region={region}',
    
    # Cost Management
    'billing': 'https://console.aws.amazon.com/billing/home',
    'cost-explorer': 'https://console.aws.amazon.com/cost-management/home',
    'budgets': 'https://console.aws.amazon.com/billing/home#/budgets',
    'cost-and-usage-report': 'https://console.aws.amazon.com/billing/home#/reports',
    'reserved-instance-reporting': 'https://console.aws.amazon.com/billing/home#/reservations',
    'savings-plans': 'https://console.aws.amazon.com/cost-management/home#/savings-plans',
    
    # Mobile Services
    'amplify': 'https://{region}.console.aws.amazon.com/amplify/home?region={region}',
    'mobile-hub': 'https://console.aws.amazon.com/mobilehub/home',
    'appsync': 'https://{region}.console.aws.amazon.com/appsync/home?region={region}',
    'device-farm': 'https://{region}.console.aws.amazon.com/devicefarm/home?region={region}',
    
    # Quantum Technologies
    'braket': 'https://{region}.console.aws.amazon.com/braket/home?region={region}',
    
    # Blockchain
    'managed-blockchain': 'https://{region}.console.aws.amazon.com/managedblockchain/home?region={region}',
    
    # Satellites
    'ground-station': 'https://{region}.console.aws.amazon.com/groundstation/home?region={region}',
    
    # Robotics
    'robomaker': 'https://{region}.console.aws.amazon.com/robomaker/home?region={region}',
    
    # Load Balancing
    'elb': 'https://{region}.console.aws.amazon.com/ec2/v2/home?region={region}#LoadBalancers:',
    'elastic-load-balancing': 'https://{region}.console.aws.amazon.com/ec2/v2/home?region={region}#LoadBalancers:',
    
    # Auto Scaling
    'auto-scaling': 'https://{region}.console.aws.amazon.com/ec2/autoscaling/home?region={region}',
    
    # Migration & Transfer
    'migration-hub': 'https://{region}.console.aws.amazon.com/migrationhub/home?region={region}',
    'application-discovery-service': 'https://{region}.console.aws.amazon.com/discovery/home?region={region}',
    'database-migration-service': 'https://{region}.console.aws.amazon.com/dms/v2/home?region={region}',
    'dms': 'https://{region}.console.aws.amazon.com/dms/v2/home?region={region}',
    'server-migration-service': 'https://{region}.console.aws.amazon.com/servermigration/home?region={region}',
    'transfer-family': 'https://{region}.console.aws.amazon.com/transfer/home?region={region}',
    'datasync': 'https://{region}.console.aws.amazon.com/datasync/home?region={region}',
    
    # Containers
    'ecr': 'https://{region}.console.aws.amazon.com/ecr/repositories?region={region}',
    'elastic-container-registry': 'https://{region}.console.aws.amazon.com/ecr/repositories?region={region}',
    
    # Customer Engagement
    'simple-email-service': 'https://{region}.console.aws.amazon.com/ses/home?region={region}',
    'ses': 'https://{region}.console.aws.amazon.com/ses/home?region={region}',
    'pinpoint': 'https://{region}.console.aws.amazon.com/pinpoint/home?region={region}',
}

# Path patterns for detecting if already on a service page
SERVICE_PATH_PATTERNS = {
    'redshift': ['/redshift/', '/redshiftv2/'],
    'athena': ['/athena/'],
    'emr': ['/emr/', '/elasticmapreduce/'],
    'quicksight': ['quicksight.aws.amazon.com'],
    'glue': ['/glue/'],
    'kinesis': ['/kinesis/', '/kinesisvideo/'],
    'batch': ['/batch/'],
    'efs': ['/efs/'],
    'fsx': ['/fsx/'],
    'elasticache': ['/elasticache/'],
    'neptune': ['/neptune/'],
    'documentdb': ['/docdb/'],
    'keyspaces': ['/keyspaces/'],
    'cognito': ['/cognito/'],
    'guardduty': ['/guardduty/'],
    'inspector': ['/inspector/'],
    'macie': ['/macie/'],
    'security-hub': ['/securityhub/'],
    'waf': ['/wafv2/'],
    'config': ['/config/'],
    'cloudformation': ['/cloudformation/'],
    'service-catalog': ['/servicecatalog/'],
    'opsworks': ['/opsworks/'],
    'step-functions': ['/states/'],
    'mq': ['/amazon-mq/'],
    'eventbridge': ['/events/'],
    'connect': ['/connect/'],
    'workspaces': ['/workspaces/'],
    'appstream': ['/appstream2/'],
    'iot-core': ['/iot/'],
    'gamelift': ['/gamelift/'],
    'amplify': ['/amplify/'],
    'appsync': ['/appsync/'],
    'braket': ['/braket/'],
    'managed-blockchain': ['/managedblockchain/'],
    'robomaker': ['/robomaker/'],
    'dms': ['/dms/'],
    'ecr': ['/ecr/'],
    'ses': ['/ses/'],
    'pinpoint': ['/pinpoint/'],
}

