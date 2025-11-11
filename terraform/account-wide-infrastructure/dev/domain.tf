
module "dev-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.dev_api_domain_name
  domain_zone                   = aws_route53_zone.dev-ns.name
  mtls_certificate_file         = "s3://${module.dev-truststore-bucket.bucket_name}/${module.dev-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.dev-truststore-bucket.certificates_object_version
  depends_on                    = [aws_route53_zone.dev-ns]
}

module "devsandbox-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.devsandbox_api_domain_name
  domain_zone                   = aws_route53_zone.dev-ns.name
  mtls_certificate_file         = "s3://${module.dev-truststore-bucket.bucket_name}/${module.dev-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.dev-truststore-bucket.certificates_object_version
  depends_on                    = [aws_route53_zone.dev-ns]
}
