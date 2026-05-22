"""
Django SECRET_KEY 安全管理工具

🔒 用途：
- 生成安全的SECRET_KEY
- 帮助运维人员配置生产环境的SECRET_KEY

⚠️ 安全提示：
- 生成SECRET_KEY后请妥善保管，不要泄露
- 定期更换SECRET_KEY（建议每年更换一次）
- 更换SECRET_KEY后需要清除所有用户会话

📝 使用方法：
1. 生成新的SECRET_KEY：python generate_secret_key.py
2. 将生成的SECRET_KEY设置到环境变量中
"""

import secrets
import string
import os

def generate_secret_key():
    """
    生成符合Django要求的SECRET_KEY
    
    Django要求SECRET_KEY至少50个字符，包含字母、数字和特殊字符
    """
    # 生成50个字符的随机字符串
    alphabet = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(50))
    
    return secret_key

def generate_django_secret():
    """
    生成Django推荐的SECRET_KEY格式
    更安全，包含更多特殊字符
    """
    # 使用Django内置方法生成
    import django
    from django.core.management.utils import get_random_secret_key
    
    return get_random_secret_key()

def main():
    print("[SECURITY] Django SECRET_KEY Generation Tool\n")
    
    print("Method 1: Standard Random Key")
    secret_key1 = generate_secret_key()
    print(f"Generated SECRET_KEY: {secret_key1}\n")
    
    print("Method 2: Django Recommended Key (Recommended)")
    secret_key2 = generate_django_secret()
    print(f"Generated SECRET_KEY: {secret_key2}\n")
    
    print("[DOC] Operations Configuration Guide:")
    print("-" * 60)
    
    print("\n[WINDOWS] Windows Server Configuration:")
    print(f"setx DJANGO_SHUASHIJUAN_SECRET_KEY \"{secret_key2}\"")
    print("(Temporary effect)")
    print(f"set DJANGO_SHUASHIJUAN_SECRET_KEY={secret_key2}")
    print("(Permanent effect, takes effect after restart)")
    
    print("\n[LINUX] Linux Server Configuration:")
    print(f"export DJANGO_SHUASHIJUAN_SECRET_KEY='{secret_key2}'")
    print("(Temporary effect, valid for current session)")
    print("Or add to ~/.bashrc or ~/.bash_profile:")
    print(f"echo \"export DJANGO_SHUASHIJUAN_SECRET_KEY='{secret_key2}'\" >> ~/.bashrc")
    
    print("\n[SYSTEMD] systemd Service Configuration:")
    print("Add to service configuration file:")
    print(f"[Service]")
    print(f"Environment=\"DJANGO_SHUASHIJUAN_SECRET_KEY={secret_key2}\"")
    
    print("\n[DOCKER] Docker Configuration:")
    print("In docker-compose.yml or Dockerfile:")
    print(f"environment:")
    print(f"  - DJANGO_SHUASHIJUAN_SECRET_KEY={secret_key2}")
    
    print("\n" + "=" * 60)
    print("[WARNING] Important Notes:")
    print("1. Please copy and save the above SECRET_KEY properly")
    print("2. Production environment MUST set DJANGO_SHUASHIJUAN_SECRET_KEY environment variable")
    print("3. Each Django project should use its own environment variable name")
    print("4. Do not submit SECRET_KEY to version control system")
    print("5. Change SECRET_KEY regularly (recommended once a year)")
    print("6. Clear user sessions after changing SECRET_KEY")
    print("=" * 60)

if __name__ == '__main__':
    main()