import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import './Landing.css'

export default function Landing() {
  const { t } = useTranslation()

  return (
    <div className="page">
      <header className="header">
        <span className="logo logo--header">{t('landing.logo')}</span>
        <nav className="links">
          <Link className="link" to="/login">{t('landing.login')}</Link>
          <Link className="link" to="/registration">{t('landing.registration')}</Link>
        </nav>
      </header>

      <section className="hero">
        <div className="hero__left">
          <h1 className="hero__title">
            {t('landing.heroTitleLine1')}<br />{t('landing.heroTitleLine2')}
          </h1>
          <Link className="hero__button" to="/registration">
            {t('landing.heroButton')}
          </Link>
        </div>
        <div className="hero__right">
          <img
            className="hero__image"
            src="/img/hero.png"
            alt={t('landing.heroImageAlt')}
          />
        </div>
      </section>

      <section className="info">
        <h2 className="info__lead">
          {t('landing.infoLeadLine1')}<br />
          {t('landing.infoLeadLine2')}<br />
          {t('landing.infoLeadLine3')}
        </h2>

        <div className="col col--now">
          <h3 className="col__title">{t('landing.colNowTitle')}</h3>
          <div className="block">
            <p className="block__label">{t('landing.blockRiskLabel')}</p>
            <p className="block__value">{t('landing.blockRiskValue')}</p>
          </div>
          <div className="block">
            <p className="block__label">{t('landing.blockSourcesLabel')}</p>
            <p className="block__value">{t('landing.blockSourcesNowValue')}</p>
          </div>
          <div className="block">
            <p className="block__label">{t('landing.blockIncomeLabel')}</p>
            <p className="block__value">{t('landing.blockIncomeNowValue')}</p>
          </div>
          <div className="block">
            <p className="block__label">{t('landing.blockFinanceLabel')}</p>
            <p className="block__value">{t('landing.blockFinanceNowValue')}</p>
          </div>
          <div className="block">
            <p className="block__label">{t('landing.blockResultLabel')}</p>
            <p className="block__value">{t('landing.blockResultNowValue')}</p>
          </div>
        </div>

        <div className="col col--with">
          <h3 className="col__title">{t('landing.colWithTitle')}</h3>
          <div className="block">
            <p className="block__label">{t('landing.blockObjectiveLabel')}</p>
            <p className="block__value">{t('landing.blockObjectiveValue')}</p>
          </div>
          <div className="block">
            <p className="block__label">{t('landing.blockSourcesLabel')}</p>
            <p className="block__value">{t('landing.blockSourcesWithValue')}</p>
          </div>
          <div className="block">
            <p className="block__label block__label--nowrap">{t('landing.blockIncomeLabel')}</p>
            <p className="block__value">{t('landing.blockIncomeWithValue')}</p>
          </div>
          <div className="block">
            <p className="block__label">{t('landing.blockFinanceLabel')}</p>
            <p className="block__value">{t('landing.blockFinanceWithValue')}</p>
          </div>
          <div className="block">
            <p className="block__label">{t('landing.blockResultLabel')}</p>
            <p className="block__value">{t('landing.blockResultWithValue')}</p>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="footer__by">
          <span className="logo logo--footer">{t('landing.logo')}</span>
          <span className="footer__text">{t('landing.footerYear')}</span>
          <span className="footer__text">{t('landing.footerBy')}</span>
        </div>
        <div className="footer__actions">
          <Link className="footer__link" to="/login">{t('landing.footerLogin')}</Link>
          <Link className="footer__link" to="/registration">{t('landing.footerRegistration')}</Link>
          <Link className="footer__link footer__link--staff" to="/loginWork">{t('landing.footerStaffLogin')}</Link>
        </div>
      </footer>
    </div>
  )
}
