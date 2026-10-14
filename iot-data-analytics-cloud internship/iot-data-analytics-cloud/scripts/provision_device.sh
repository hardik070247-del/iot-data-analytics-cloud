#!/usr/bin/env bash
# Creates an IoT Thing + certificate, attaches the policy, downloads certs to ./certs
set -euo pipefail
THING=${1:-iot-sim-publisher}
POLICY=${2:-iot-sim-device-policy}
mkdir -p certs

aws iot create-thing --thing-name "$THING" >/dev/null
CERT_ARN=$(aws iot create-keys-and-certificate --set-as-active \
  --certificate-pem-outfile certs/device.pem.crt \
  --private-key-outfile certs/private.pem.key \
  --query certificateArn --output text)
aws iot attach-policy --policy-name "$POLICY" --target "$CERT_ARN"
aws iot attach-thing-principal --thing-name "$THING" --principal "$CERT_ARN"
curl -s -o certs/AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem

echo "Endpoint:"
aws iot describe-endpoint --endpoint-type iot:Data-ATS --query endpointAddress --output text
