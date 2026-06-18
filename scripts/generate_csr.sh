#!/usr/bin/env bash
set -euo pipefail

HERE=$(dirname "$0")
VALIDATOR="$HERE/validate_icp_fields.py"

usage(){
  cat <<EOF
Usage: $0 \
  --nome "NOME COMPLETO" --cpf CPF --nascimento DDMMAAAA --nis NIS --rg RG --orgao-uf SSPRS \
  --cei CEI --titulo TITULO --zona ZONA --secao SECAO --municipio-uf "MUNICIPIO UF" \
  [--outdir DIR] [--encrypt]

Gera chave RSA 2048 e CSR (PKCS#10) com SubjectAltName otherName para PF A3 ICP-Brasil.
Quando --encrypt e usado, a chave privada e protegida com AES-256 (sera solicitada senha).
EOF
}

OUTDIR="/tmp/icp_test"
ENCRYPT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --nome) NOME="$2"; shift 2;;
    --cpf) CPF="$2"; shift 2;;
    --nascimento) NASCIMENTO="$2"; shift 2;;
    --nis) NIS="$2"; shift 2;;
    --rg) RG="$2"; shift 2;;
    --orgao-uf) ORGAO_UF="$2"; shift 2;;
    --cei) CEI="$2"; shift 2;;
    --titulo) TITULO="$2"; shift 2;;
    --zona) ZONA="$2"; shift 2;;
    --secao) SECAO="$2"; shift 2;;
    --municipio-uf) MUNICIPIO_UF="$2"; shift 2;;
    --outdir) OUTDIR="$2"; shift 2;;
    --encrypt) ENCRYPT=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "${NOME:-}" || -z "${CPF:-}" || -z "${NASCIMENTO:-}" || -z "${NIS:-}" || -z "${RG:-}" || -z "${ORGAO_UF:-}" || -z "${CEI:-}" || -z "${TITULO:-}" || -z "${ZONA:-}" || -z "${SECAO:-}" || -z "${MUNICIPIO_UF:-}" ]]; then
  echo "Missing required args." >&2
  usage
  exit 1
fi

mkdir -p "$OUTDIR"
KEY_FILE="$OUTDIR/key.pem"
CSR_FILE="$OUTDIR/req.csr"

# Call validator to build SAN/CN
SAN=$("$(command -v python3)" "$VALIDATOR" \
  --nome "$NOME" --cpf "$CPF" --nascimento "$NASCIMENTO" --nis "$NIS" --rg "$RG" --orgao-uf "$ORGAO_UF" \
  --cei "$CEI" --titulo "$TITULO" --zona "$ZONA" --secao "$SECAO" --municipio-uf "$MUNICIPIO_UF" --output san)

CN=$("$(command -v python3)" "$VALIDATOR" \
  --nome "$NOME" --cpf "$CPF" --nascimento "$NASCIMENTO" --nis "$NIS" --rg "$RG" --orgao-uf "$ORGAO_UF" \
  --cei "$CEI" --titulo "$TITULO" --zona "$ZONA" --secao "$SECAO" --municipio-uf "$MUNICIPIO_UF" --output cn)

echo "Generating CSR in $OUTDIR"

if [[ "$ENCRYPT" -eq 1 ]]; then
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -aes-256-cbc -out "$KEY_FILE"
else
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$KEY_FILE"
fi

openssl req -new -key "$KEY_FILE" \
  -subj "/C=BR/O=ICP-Brasil/OU=AC DIGITAL Multipla G1/OU=33989214000191/OU=presencial/OU=Certificado PF A3/CN=$CN" \
  -addext "subjectAltName=$SAN" \
  -out "$CSR_FILE"

echo "Key: $KEY_FILE"
echo "CSR: $CSR_FILE"
echo "subjectAltName used: $SAN"
echo "\nInspect with: openssl req -in $CSR_FILE -noout -text"
