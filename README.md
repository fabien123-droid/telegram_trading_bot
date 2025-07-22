# Telegram Trading Bot

Un bot de trading automatisé multi-utilisateurs pour Telegram avec intégration de brokers multiples et analyse technique avancée.

## 🚀 Fonctionnalités

### Trading Automatisé
- **Multi-brokers** : Support pour Deriv, Binance, MetaTrader 5, et Interactive Brokers
- **Signaux intelligents** : Analyse technique combinée avec sentiment de marché
- **Gestion des risques** : Stop-loss, take-profit, et dimensionnement automatique des positions
- **Trading manuel et automatique** : Contrôle total sur vos trades

### Analyse Technique Avancée
- **Indicateurs techniques** : RSI, MACD, Bollinger Bands, Stochastic
- **Support/Résistance** : Détection automatique des niveaux clés
- **Analyse de sentiment** : Intégration des nouvelles et sentiment du marché
- **Signaux multi-timeframes** : Analyse sur plusieurs périodes

### Interface Telegram Intuitive
- **Commandes simples** : Interface utilisateur conviviale
- **Notifications en temps réel** : Alertes pour signaux et trades
- **Tableaux de bord** : Suivi des performances et positions
- **Configuration flexible** : Personnalisation complète des paramètres

### Sécurité et Multi-utilisateurs
- **Chiffrement des données** : Credentials des brokers chiffrés
- **Gestion multi-utilisateurs** : Chaque utilisateur avec ses propres comptes
- **Sessions sécurisées** : Authentification et autorisation robustes
- **Journalisation complète** : Traçabilité de toutes les opérations

## 📋 Prérequis

- Python 3.11+
- Base de données SQLite (ou PostgreSQL pour la production)
- Comptes brokers (Deriv, Binance, etc.)
- Bot Telegram et token API

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd telegram_trading_bot
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configuration
Copiez le fichier de configuration d'exemple :
```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos paramètres :
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook

# Database
DATABASE_URL=sqlite:///trading_bot.db

# Security
SECRET_KEY=your_secret_key_here

# Deriv API
DERIV_APP_ID=your_deriv_app_id
DERIV_API_URL=wss://ws.binaryws.com/websockets/v3

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log
```

### 4. Initialiser la base de données
```bash
python -c "from database.database import init_database; import asyncio; asyncio.run(init_database())"
```

### 5. Lancer le bot
```bash
python main.py
```

## 🔧 Configuration des Brokers

### Deriv
1. Créez un compte sur [Deriv.com](https://deriv.com)
2. Générez un token API dans les paramètres
3. Ajoutez le token via la commande `/account` du bot

### Binance
1. Créez un compte sur [Binance.com](https://binance.com)
2. Générez une clé API avec permissions de trading
3. Ajoutez les credentials via `/account`

### MetaTrader 5
1. Installez MT5 et créez un compte
2. Activez l'API dans les paramètres
3. Configurez les paramètres de connexion

### Interactive Brokers
1. Créez un compte IB
2. Installez TWS ou IB Gateway
3. Configurez les paramètres de connexion API

## 📱 Utilisation

### Commandes Principales

- `/start` - Démarrer le bot et voir le menu principal
- `/account` - Gérer les comptes brokers
- `/settings` - Configurer les paramètres de trading
- `/trading` - Centre de trading et contrôles
- `/signals` - Voir les signaux actuels
- `/history` - Historique des trades
- `/help` - Aide et documentation

### Configuration des Paramètres

#### Gestion des Risques
- **Risque par trade** : 1-5% du capital (recommandé : 2%)
- **Positions maximum** : Nombre de positions simultanées
- **Stop-loss par défaut** : Pourcentage de perte acceptable
- **Take-profit par défaut** : Objectif de profit

#### Signaux
- **Force minimum** : Filtrer les signaux faibles
- **Poids technique** : Importance de l'analyse technique (70%)
- **Poids sentiment** : Importance du sentiment (30%)

#### Notifications
- **Alertes signaux** : Notifications pour nouveaux signaux
- **Alertes trades** : Notifications d'exécution
- **Résumé quotidien** : Rapport de performance

## 🏗️ Architecture

### Structure du Projet
```
telegram_trading_bot/
├── core/                   # Configuration et utilitaires
├── telegram_bot/          # Interface Telegram
├── trading/               # Logique de trading
│   └── brokers/          # Intégrations brokers
├── analysis/             # Analyse technique et sentiment
├── database/             # Modèles et accès données
├── security/             # Chiffrement et sécurité
├── tests/               # Tests unitaires
└── docs/                # Documentation
```

### Modules Principaux

#### Core
- **Configuration** : Gestion centralisée des paramètres
- **Exceptions** : Gestion d'erreurs personnalisées
- **Utilitaires** : Fonctions communes
- **Logging** : Journalisation structurée

#### Trading
- **Base Broker** : Interface commune pour tous les brokers
- **Deriv Broker** : Intégration API Deriv
- **Binance Broker** : Intégration API Binance
- **Order Manager** : Gestion des ordres et positions

#### Analysis
- **Technical Indicators** : Calcul des indicateurs techniques
- **Sentiment Analysis** : Analyse du sentiment de marché
- **Signal Generator** : Génération de signaux de trading
- **Data Fetcher** : Récupération des données de marché

#### Database
- **Models** : Modèles de données SQLAlchemy
- **Repositories** : Couche d'accès aux données
- **Migrations** : Gestion des versions de base de données

## 🧪 Tests

### Lancer les tests
```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_technical_indicators.py
pytest tests/test_brokers.py

# Avec couverture
pytest --cov=. --cov-report=html
```

### Types de Tests
- **Tests unitaires** : Fonctions individuelles
- **Tests d'intégration** : Interaction entre modules
- **Tests de performance** : Optimisation et vitesse
- **Tests de sécurité** : Validation des mesures de sécurité

## 📊 Monitoring et Logs

### Logs
Les logs sont organisés par niveaux :
- **DEBUG** : Informations détaillées pour le développement
- **INFO** : Événements normaux du système
- **WARNING** : Situations potentiellement problématiques
- **ERROR** : Erreurs qui n'arrêtent pas le système
- **CRITICAL** : Erreurs critiques nécessitant une intervention

### Métriques
- **Performance des signaux** : Taux de réussite et précision
- **Statistiques de trading** : P&L, win rate, drawdown
- **Utilisation système** : CPU, mémoire, connexions
- **Activité utilisateurs** : Commandes, trades, erreurs

## 🔒 Sécurité

### Chiffrement
- **Credentials brokers** : Chiffrés avec Fernet (AES 128)
- **Sessions utilisateurs** : Tokens sécurisés
- **Communications** : HTTPS/WSS uniquement

### Bonnes Pratiques
- **Validation des entrées** : Sanitisation de toutes les données
- **Gestion des erreurs** : Pas d'exposition d'informations sensibles
- **Audit trail** : Journalisation de toutes les actions
- **Rate limiting** : Protection contre les abus

## 🚀 Déploiement

### Production
1. **Serveur** : VPS ou cloud (AWS, DigitalOcean, etc.)
2. **Base de données** : PostgreSQL recommandé
3. **Reverse proxy** : Nginx pour HTTPS
4. **Process manager** : systemd ou PM2
5. **Monitoring** : Prometheus + Grafana

### Docker (Optionnel)
```bash
# Build
docker build -t telegram-trading-bot .

# Run
docker run -d --name trading-bot \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  telegram-trading-bot
```

### Variables d'Environnement Production
```env
# Production settings
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@localhost/trading_bot
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your_sentry_dsn
```

## 📈 Stratégies de Trading

### Stratégies Intégrées

#### Conservative
- Signaux forts uniquement (confidence > 80%)
- Stop-loss serré (1-2%)
- Take-profit modéré (2-3%)
- Maximum 3 positions simultanées

#### Moderate
- Signaux modérés et forts (confidence > 60%)
- Stop-loss standard (2-3%)
- Take-profit équilibré (3-5%)
- Maximum 5 positions simultanées

#### Aggressive
- Tous signaux (confidence > 40%)
- Stop-loss large (3-5%)
- Take-profit élevé (5-8%)
- Maximum 10 positions simultanées

### Personnalisation
Vous pouvez créer vos propres stratégies en modifiant :
- **Filtres de signaux** : Critères de sélection
- **Gestion des risques** : Tailles de position et stops
- **Timeframes** : Périodes d'analyse
- **Indicateurs** : Combinaisons personnalisées

## 🤝 Contribution

### Comment Contribuer
1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Standards de Code
- **PEP 8** : Style de code Python
- **Type hints** : Annotations de type obligatoires
- **Docstrings** : Documentation des fonctions
- **Tests** : Couverture minimum 80%

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## ⚠️ Avertissement

**Le trading comporte des risques financiers importants. Ce bot est fourni à des fins éducatives et de recherche. L'utilisation de ce logiciel pour le trading réel est à vos propres risques. Les développeurs ne sont pas responsables des pertes financières.**

### Recommandations
- **Testez d'abord** : Utilisez les comptes de démonstration
- **Commencez petit** : Investissez seulement ce que vous pouvez perdre
- **Surveillez activement** : Le bot n'est pas infaillible
- **Éduquez-vous** : Comprenez les marchés et les risques

## 📞 Support

### Documentation
- **Wiki** : Documentation détaillée
- **API Reference** : Documentation des APIs
- **Tutorials** : Guides pas à pas

### Communauté
- **GitHub Issues** : Bugs et demandes de fonctionnalités
- **Discussions** : Questions et partage d'expériences
- **Telegram Group** : Support communautaire

### Contact
- **Email** : support@tradingbot.com
- **Telegram** : @TradingBotSupport

---

**Développé avec ❤️ par l'équipe Trading Bot**

