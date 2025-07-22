# Guide d'Installation - Telegram Trading Bot

Ce guide vous accompagne pas à pas dans l'installation et la configuration du bot de trading Telegram.

## 📋 Prérequis Système

### Système d'Exploitation
- **Linux** : Ubuntu 20.04+ (recommandé), CentOS 8+, Debian 11+
- **Windows** : Windows 10/11 avec WSL2
- **macOS** : macOS 11+ (Big Sur)

### Logiciels Requis
- **Python** : Version 3.11 ou supérieure
- **pip** : Gestionnaire de paquets Python
- **Git** : Pour cloner le repository
- **Base de données** : SQLite (inclus) ou PostgreSQL (production)

### Ressources Minimales
- **RAM** : 2 GB minimum, 4 GB recommandé
- **Stockage** : 5 GB d'espace libre
- **Réseau** : Connexion internet stable
- **CPU** : 2 cœurs minimum

## 🔧 Installation Étape par Étape

### Étape 1 : Préparation de l'Environnement

#### Sur Ubuntu/Debian
```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système
sudo apt install -y python3.11 python3.11-pip python3.11-venv git curl wget

# Vérification de la version Python
python3.11 --version
```

#### Sur CentOS/RHEL
```bash
# Installation des dépendances
sudo dnf install -y python3.11 python3.11-pip git curl wget

# Ou avec yum sur les versions plus anciennes
sudo yum install -y python3.11 python3.11-pip git curl wget
```

#### Sur Windows (WSL2)
```bash
# Dans WSL2 Ubuntu
sudo apt update
sudo apt install -y python3.11 python3.11-pip python3.11-venv git
```

#### Sur macOS
```bash
# Avec Homebrew
brew install python@3.11 git

# Vérification
python3.11 --version
```

### Étape 2 : Téléchargement du Code

```bash
# Cloner le repository
git clone https://github.com/your-username/telegram-trading-bot.git
cd telegram-trading-bot

# Ou télécharger et extraire l'archive ZIP
wget https://github.com/your-username/telegram-trading-bot/archive/main.zip
unzip main.zip
cd telegram-trading-bot-main
```

### Étape 3 : Création de l'Environnement Virtuel

```bash
# Créer l'environnement virtuel
python3.11 -m venv venv

# Activer l'environnement virtuel
# Sur Linux/macOS
source venv/bin/activate

# Sur Windows
# venv\Scripts\activate
```

### Étape 4 : Installation des Dépendances

```bash
# Mise à jour de pip
pip install --upgrade pip

# Installation des dépendances
pip install -r requirements.txt

# Vérification de l'installation
pip list
```

### Étape 5 : Configuration

#### Copie du Fichier de Configuration
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer la configuration
nano .env  # ou vim, code, etc.
```

#### Configuration Minimale
Éditez le fichier `.env` avec vos paramètres :

```env
# === CONFIGURATION TELEGRAM ===
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook

# === BASE DE DONNÉES ===
DATABASE_URL=sqlite:///data/trading_bot.db
DATABASE_ECHO=false

# === SÉCURITÉ ===
SECRET_KEY=your_very_long_and_secure_secret_key_here

# === DERIV API ===
DERIV_APP_ID=1089
DERIV_API_URL=wss://ws.binaryws.com/websockets/v3

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# === ENVIRONNEMENT ===
ENVIRONMENT=development
DEBUG=true
```

### Étape 6 : Création des Répertoires

```bash
# Créer les répertoires nécessaires
mkdir -p data logs backups

# Définir les permissions
chmod 755 data logs backups
```

### Étape 7 : Initialisation de la Base de Données

```bash
# Initialiser la base de données
python -c "
import asyncio
from database.database import init_database
asyncio.run(init_database())
"

# Vérifier la création des tables
ls -la data/
```

### Étape 8 : Test de l'Installation

```bash
# Test de base
python -c "
import sys
print(f'Python version: {sys.version}')

from core.config import get_settings
settings = get_settings()
print(f'Configuration loaded: {settings.app.name}')

from database.database import DatabaseHealthCheck
import asyncio
result = asyncio.run(DatabaseHealthCheck.check_connection())
print(f'Database connection: {result}')
"
```

## 🤖 Configuration du Bot Telegram

### Étape 1 : Créer un Bot Telegram

1. **Ouvrez Telegram** et recherchez `@BotFather`
2. **Démarrez une conversation** avec BotFather
3. **Créez un nouveau bot** :
   ```
   /newbot
   ```
4. **Choisissez un nom** pour votre bot (ex: "Mon Trading Bot")
5. **Choisissez un username** (ex: "mon_trading_bot")
6. **Copiez le token** fourni par BotFather

### Étape 2 : Configuration du Bot

```bash
# Éditer la configuration
nano .env

# Ajouter le token
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Étape 3 : Configuration des Commandes

Envoyez à BotFather :
```
/setcommands
```

Puis copiez-collez ces commandes :
```
start - Démarrer le bot
account - Gérer les comptes brokers
settings - Paramètres de trading
trading - Centre de trading
signals - Signaux actuels
history - Historique des trades
status - Statut du bot
help - Aide et documentation
```

## 🏦 Configuration des Brokers

### Deriv

#### Étape 1 : Créer un Compte
1. Allez sur [Deriv.com](https://deriv.com)
2. Créez un compte de démonstration ou réel
3. Vérifiez votre email

#### Étape 2 : Générer un Token API
1. Connectez-vous à votre compte Deriv
2. Allez dans **Paramètres** → **API Token**
3. Cliquez sur **Créer un nouveau token**
4. Sélectionnez les permissions :
   - ✅ Read
   - ✅ Trade
   - ✅ Trading information
   - ✅ Payments
5. Copiez le token généré

#### Étape 3 : Tester la Connexion
```bash
python -c "
import asyncio
from trading.brokers.deriv_broker import DerivBroker

async def test_deriv():
    broker = DerivBroker({'api_token': 'YOUR_TOKEN_HERE'})
    try:
        await broker.connect()
        account = await broker.get_account_info()
        print(f'Connexion réussie! Balance: {account.balance} {account.currency}')
        await broker.disconnect()
    except Exception as e:
        print(f'Erreur: {e}')

asyncio.run(test_deriv())
"
```

### Binance

#### Étape 1 : Créer un Compte
1. Allez sur [Binance.com](https://binance.com)
2. Créez un compte
3. Activez l'authentification 2FA

#### Étape 2 : Créer une Clé API
1. Allez dans **Profil** → **Sécurité API**
2. Cliquez sur **Créer une API**
3. Nommez votre API (ex: "Trading Bot")
4. Activez les permissions :
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ✅ Enable Futures Trading (optionnel)
5. Copiez la **API Key** et la **Secret Key**

#### Étape 3 : Configuration Testnet (Recommandé)
1. Allez sur [Testnet Binance](https://testnet.binance.vision)
2. Connectez-vous avec GitHub
3. Créez une clé API testnet
4. Utilisez ces credentials pour les tests

## 🚀 Premier Lancement

### Étape 1 : Lancement en Mode Test

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le bot en mode debug
python main.py --debug

# Ou avec logging détaillé
python main.py --log-level DEBUG
```

### Étape 2 : Vérification du Fonctionnement

1. **Ouvrez Telegram** et recherchez votre bot
2. **Démarrez une conversation** avec `/start`
3. **Testez les commandes** de base :
   - `/help` - Affiche l'aide
   - `/status` - Vérifie le statut
   - `/account` - Gestion des comptes

### Étape 3 : Configuration Initiale

1. **Ajoutez un compte broker** :
   ```
   /account
   → Ajouter un compte
   → Choisir Deriv
   → Entrer votre token API
   ```

2. **Configurez les paramètres** :
   ```
   /settings
   → Gestion des risques
   → Risque par trade: 2%
   → Stop-loss: 2%
   → Take-profit: 4%
   ```

3. **Testez les signaux** :
   ```
   /signals
   → Voir les signaux actuels
   ```

## 🔧 Configuration Avancée

### Base de Données PostgreSQL (Production)

#### Installation PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo dnf install postgresql postgresql-server postgresql-contrib

# Démarrer le service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Configuration
```bash
# Créer un utilisateur et une base
sudo -u postgres psql

CREATE USER trading_bot WITH PASSWORD 'secure_password';
CREATE DATABASE trading_bot OWNER trading_bot;
GRANT ALL PRIVILEGES ON DATABASE trading_bot TO trading_bot;
\q
```

#### Mise à Jour de la Configuration
```env
# Dans .env
DATABASE_URL=postgresql://trading_bot:secure_password@localhost/trading_bot
```

### Configuration HTTPS/SSL

#### Avec Nginx
```nginx
# /etc/nginx/sites-available/trading-bot
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Service Systemd

#### Créer le Service
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

```ini
[Unit]
Description=Telegram Trading Bot
After=network.target

[Service]
Type=simple
User=trading-bot
WorkingDirectory=/home/trading-bot/telegram-trading-bot
Environment=PATH=/home/trading-bot/telegram-trading-bot/venv/bin
ExecStart=/home/trading-bot/telegram-trading-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Activer le Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

## 🐛 Résolution des Problèmes

### Problèmes Courants

#### Erreur d'Import Python
```bash
# Vérifier l'environnement virtuel
which python
pip list

# Réinstaller les dépendances
pip install --force-reinstall -r requirements.txt
```

#### Erreur de Base de Données
```bash
# Vérifier les permissions
ls -la data/
chmod 755 data/

# Réinitialiser la base
rm data/trading_bot.db
python -c "from database.database import init_database; import asyncio; asyncio.run(init_database())"
```

#### Erreur de Connexion Broker
```bash
# Tester la connectivité
ping api.binance.com
ping ws.binaryws.com

# Vérifier les credentials
python -c "
from security.encryption import decrypt_data
# Test de déchiffrement
"
```

#### Erreur Telegram
```bash
# Vérifier le token
curl -X GET "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Tester le webhook
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook"}'
```

### Logs et Debugging

#### Activer les Logs Détaillés
```env
# Dans .env
LOG_LEVEL=DEBUG
DEBUG=true
```

#### Consulter les Logs
```bash
# Logs en temps réel
tail -f logs/trading_bot.log

# Rechercher des erreurs
grep -i error logs/trading_bot.log

# Logs par date
grep "2024-01-15" logs/trading_bot.log
```

### Performance et Optimisation

#### Monitoring des Ressources
```bash
# Utilisation CPU/RAM
top -p $(pgrep -f "python main.py")

# Connexions réseau
netstat -tulpn | grep python

# Espace disque
du -sh data/ logs/
```

#### Optimisation Base de Données
```sql
-- Analyser les performances
EXPLAIN ANALYZE SELECT * FROM trades WHERE user_id = 1;

-- Nettoyer les anciennes données
DELETE FROM system_logs WHERE created_at < NOW() - INTERVAL '30 days';
```

## 📚 Ressources Supplémentaires

### Documentation
- **API Deriv** : [developers.deriv.com](https://developers.deriv.com)
- **API Binance** : [binance-docs.github.io](https://binance-docs.github.io)
- **Telegram Bot API** : [core.telegram.org/bots/api](https://core.telegram.org/bots/api)

### Outils Utiles
- **Postman** : Test des APIs
- **pgAdmin** : Administration PostgreSQL
- **Grafana** : Monitoring et dashboards
- **Sentry** : Tracking des erreurs

### Communauté
- **GitHub Issues** : Signaler des bugs
- **Discussions** : Poser des questions
- **Wiki** : Documentation communautaire

---

**Installation terminée ! Votre bot de trading est maintenant prêt à fonctionner. 🎉**

Pour toute question ou problème, consultez la section [Résolution des Problèmes](#-résolution-des-problèmes) ou contactez le support.

