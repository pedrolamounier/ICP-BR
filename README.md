# ICP-BR
ICP-BR Certificate generation

## Geração segura de CSR (PF A3)

Scripts:

- `scripts/validate_icp_fields.py`: valida/formata campos ICP-Brasil PF A3.
- `scripts/generate_csr.sh`: gera chave RSA 2048 e CSR PKCS#10 com `subjectAltName` (`otherName`).

Requisitos:

- OpenSSL 1.1.1+ (testado com OpenSSL 3.5.5)
- Python 3

Exemplo:

```bash
chmod +x scripts/generate_csr.sh

scripts/generate_csr.sh \
	--nome "FULANO DE TAL" \
	--cpf "52998224725" \
	--nascimento "17121953" \
	--nis "12345678901" \
	--rg "5784212" \
	--orgao-uf "SSPRS" \
	--cei "253764977686" \
	--titulo "465555610469" \
	--zona "001" \
	--secao "0477" \
	--municipio-uf "PORTO ALEGRE RS" \
	--outdir "/tmp/icp_test" \
	--encrypt
```

Depois, valide o CSR:

```bash
openssl req -in /tmp/icp_test/req.csr -noout -text
```

Notas:

- `--encrypt` protege a chave privada com AES-256 e solicita senha no terminal.
- O script valida CPF por digito verificador e normaliza textos para caracteres ASCII.
- A emissao final do certificado A3 depende da AC e do uso de dispositivo homologado (token/cartao/HSM), conforme a politica da ICP-Brasil.
