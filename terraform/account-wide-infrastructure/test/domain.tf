
module "qa-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.qa_api_domain_name
  domain_zone                   = aws_route53_zone.test-qa-ns.name
  mtls_certificate_file         = "s3://${module.qa-truststore-bucket.bucket_name}/${module.qa-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.qa-truststore-bucket.certificates_object_version
}

module "qasandbox-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.qasandbox_api_domain_name
  domain_zone                   = aws_route53_zone.test-qa-ns.name
  mtls_certificate_file         = "s3://${module.qa-truststore-bucket.bucket_name}/${module.qa-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.qa-truststore-bucket.certificates_object_version
}

module "int-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.int_api_domain_name
  domain_zone                   = aws_route53_zone.test-int-ns.name
  mtls_certificate_file         = "s3://${module.int-truststore-bucket.bucket_name}/${module.int-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.int-truststore-bucket.certificates_object_version
}

module "intsandbox-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.intsandbox_api_domain_name
  domain_zone                   = aws_route53_zone.test-int-ns.name
  mtls_certificate_file         = "s3://${module.int-truststore-bucket.bucket_name}/${module.int-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.int-truststore-bucket.certificates_object_version
}

module "ref-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.ref_api_domain_name
  domain_zone                   = aws_route53_zone.test-ref-ns.name
  mtls_certificate_file         = "s3://${module.ref-truststore-bucket.bucket_name}/${module.ref-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.ref-truststore-bucket.certificates_object_version
}

module "perftest-custom-domain-name" {
  source                        = "../modules/env-custom-domain-name"
  domain_name                   = var.perftest_api_domain_name
  domain_zone                   = aws_route53_zone.test-perftest-ns.name
  mtls_certificate_file         = "s3://${module.perftest-truststore-bucket.bucket_name}/${module.perftest-truststore-bucket.certificates_object_key}"
  mtls_certificate_file_version = module.perftest-truststore-bucket.certificates_object_version
}
