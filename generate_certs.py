"""
Script para generar certificados SSL autofirmados para la comunicación segura.
Ejecutar una vez antes de iniciar el servidor y cliente.
"""
import subprocess
import os
import sys

# Directorio actual
CERT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(CERT_DIR, "server.crt")
KEY_FILE = os.path.join(CERT_DIR, "server.key")


def generate_certificates():
    """Genera certificados SSL autofirmados usando OpenSSL o cryptography"""
    
    # Verificar si ya existen los certificados
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        print("✅ Los certificados ya existen:")
        print(f"   - Certificado: {CERT_FILE}")
        print(f"   - Clave privada: {KEY_FILE}")
        
        response = input("\n¿Desea regenerarlos? (s/n): ").strip().lower()
        if response != 's':
            print("Usando certificados existentes.")
            return True
    
    print("\n🔐 Generando certificados SSL autofirmados...")
    
    try:
        # Intentar usar la biblioteca cryptography (más portable)
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        # Generar clave privada RSA
        print("   Generando clave privada RSA (2048 bits)...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Crear certificado autofirmado
        print("   Creando certificado autofirmado...")
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "San Jose"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Jose"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Red Social TEC"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Guardar clave privada
        print(f"   Guardando clave privada en: {KEY_FILE}")
        with open(KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Guardar certificado
        print(f"   Guardando certificado en: {CERT_FILE}")
        with open(CERT_FILE, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("\n✅ Certificados generados exitosamente!")
        print(f"   - Certificado: {CERT_FILE}")
        print(f"   - Clave privada: {KEY_FILE}")
        print("\n⚠️  NOTA: Estos son certificados autofirmados para desarrollo.")
        print("   Para producción, use certificados de una CA confiable.")
        return True
        
    except ImportError:
        print("⚠️  La biblioteca 'cryptography' no está instalada.")
        print("   Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        print("\n🔄 Por favor, ejecute este script nuevamente.")
        return False
    except Exception as e:
        print(f"❌ Error generando certificados: {e}")
        return False


# Necesitamos importar ipaddress para la extensión SAN
import ipaddress

if __name__ == "__main__":
    print("=" * 50)
    print("   GENERADOR DE CERTIFICADOS SSL")
    print("=" * 50)
    
    if generate_certificates():
        print("\n✅ Listo! Ahora puede iniciar el servidor y cliente de forma segura.")
    else:
        print("\n❌ No se pudieron generar los certificados.")
        sys.exit(1)
