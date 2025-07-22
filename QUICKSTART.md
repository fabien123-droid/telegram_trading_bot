# 🚀 Démarrage Rapide - Telegram Trading Bot

Ce guide vous permet de démarrer le bot en moins de 10 minutes !

## ⚡ Installation Express

### Prérequis
- Python 3.11+
- Un compte Telegram
- Un compte broker (Deriv recommandé pour commencer)

### 1. Téléchargement
```bash
# Cloner ou télécharger le projet
git clone <repository-url>
cd telegram_trading_bot

# Ou extraire l'archive ZIP
unzip telegram_trading_bot.zip
cd telegram_trading_bot
```

### 2. Installation
```bash
# Créer l'environnement virtuel
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration Minimale
```bash
# Copier la configuration
cp .env.example .env

# Éditer avec vos paramètres
nano .env  # ou votre éditeur préféré
```

**Configuration minimale requise :**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///data/trading_bot.db
```

### 4. Initialisation
```bash
# Créer les répertoires
mkdir -p data logs

# Initialiser la base de données
python -c "
import asyncio
from database.database import init_database
asyncio.run(init_database())
"
```

### 5. Lancement
```bash
python main.py
```

## 🤖 Configuration du Bot Telegram

### Créer le Bot
1. Ouvrez Telegram et cherchez `@BotFather`
2. Tapez `/newbot`
3. Choisissez un nom : "Mon Trading Bot"
4. Choisissez un username : "mon_trading_bot"
5. Copiez le token dans votre `.env`

### Première Utilisation
1. Cherchez votre bot dans Telegram
2. Tapez `/start`
3. Suivez les instructions à l'écran

## 🏦 Configuration Broker (Deriv)

### Créer un Compte Deriv
1. Allez sur [deriv.com](https://deriv.com)
2. Créez un compte de démonstration
3. Vérifiez votre email

### Obtenir le Token API
1. Connectez-vous à Deriv
2. Allez dans **Paramètres** → **API Token**
3. Créez un token avec permissions :
   - ✅ Read
   - ✅ Trade
   - ✅ Trading information
4. Copiez le token

### Ajouter le Compte
1. Dans Telegram, tapez `/account`
2. Choisissez "Ajouter un compte"
3. Sélectionnez "Deriv"
4. Collez votre token API

## ⚙️ Configuration Rapide

### Paramètres Recommandés pour Débuter
```
/settings

Gestion des Risques:
- Risque par trade: 1%
- Positions max: 3
- Stop-loss: 2%
- Take-profit: 4%

Signaux:
- Force minimum: Modéré
- Auto-trading: Désactivé (pour commencer)
```

## 🎯 Premier Trade

### Mode Manuel (Recommandé)
1. Tapez `/signals` pour voir les signaux
2. Analysez les recommandations
3. Tapez `/trading` → "Trade Manuel"
4. Suivez les instructions

### Mode Automatique (Avancé)
1. Configurez d'abord vos paramètres
2. Testez en mode manuel
3. Activez l'auto-trading : `/settings` → "Auto Trading"

## 📊 Surveillance

### Commandes Utiles
- `/status` - État du bot et connexions
- `/history` - Historique des trades
- `/signals` - Signaux actuels
- `/account` - État des comptes

### Notifications
Le bot vous enverra automatiquement :
- 📈 Nouveaux signaux de trading
- 💰 Confirmations d'exécution
- ⚠️ Alertes importantes
- 📊 Résumé quotidien

## 🔧 Résolution Rapide des Problèmes

### Le bot ne répond pas
```bash
# Vérifier les logs
tail -f logs/trading_bot.log

# Redémarrer
python main.py
```

### Erreur de connexion broker
1. Vérifiez votre token API
2. Testez la connexion : `/account` → "Tester"
3. Régénérez le token si nécessaire

### Pas de signaux
1. Vérifiez les paramètres : `/settings`
2. Assurez-vous que les marchés sont ouverts
3. Réduisez la force minimum des signaux

## 🚀 Déploiement Production (Optionnel)

### Avec Docker
```bash
# Build et lancement
docker-compose up -d

# Vérifier les logs
docker-compose logs -f trading-bot
```

### Sur VPS
```bash
# Installer comme service
sudo cp trading-bot.service /etc/systemd/system/
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

## 📚 Ressources

### Documentation
- **README.md** - Documentation complète
- **INSTALLATION.md** - Guide d'installation détaillé
- **API Documentation** - Référence des APIs

### Support
- **GitHub Issues** - Signaler des bugs
- **Telegram Group** - Support communautaire
- **Email** - support@tradingbot.com

### Sécurité
- **Testez d'abord** avec des comptes de démonstration
- **Commencez petit** avec des montants faibles
- **Surveillez activement** vos trades
- **Ne tradez jamais** plus que vous ne pouvez perdre

## ✅ Checklist de Démarrage

- [ ] Python 3.11+ installé
- [ ] Projet téléchargé et dépendances installées
- [ ] Bot Telegram créé et token configuré
- [ ] Compte broker créé (Deriv recommandé)
- [ ] Token API broker obtenu
- [ ] Base de données initialisée
- [ ] Bot lancé et fonctionnel
- [ ] Compte broker ajouté dans le bot
- [ ] Paramètres de base configurés
- [ ] Premier test de signal effectué

## 🎉 Félicitations !

Votre bot de trading est maintenant opérationnel ! 

**Prochaines étapes :**
1. Familiarisez-vous avec l'interface
2. Testez les signaux en mode manuel
3. Ajustez les paramètres selon vos préférences
4. Explorez les fonctionnalités avancées

**Rappel important :** Commencez toujours avec des comptes de démonstration et des montants faibles pour vous familiariser avec le système.

---

**Besoin d'aide ?** Consultez la documentation complète ou contactez le support !

