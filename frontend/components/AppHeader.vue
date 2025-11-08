<template>
  <header class="app-header">
    <div class="header-container">
      <div class="logo">
        <NuxtLink to="/">
          <span class="logo-icon">✈️</span>
          <span class="logo-text">Flights Scanner</span>
        </NuxtLink>
      </div>

      <nav class="nav-menu">
        <NuxtLink to="/" class="nav-link">
          Home
        </NuxtLink>
        <NuxtLink to="/price-chart" class="nav-link">
          Price Chart
        </NuxtLink>
        <NuxtLink to="/trip-search" class="nav-link">
          Trip Search
        </NuxtLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: white;
  font-size: 1.5rem;
  font-weight: 700;
  transition: transform 0.2s;
}

.logo a:hover {
  transform: translateY(-2px);
}

.logo-icon {
  font-size: 2rem;
}

.logo-text {
  font-size: 1.5rem;
}

.nav-menu {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  font-weight: 500;
  font-size: 1.1rem;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  transition: all 0.2s;
  position: relative;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.15);
}

.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.2);
  font-weight: 600;
}

@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .nav-menu {
    gap: 1rem;
  }

  .logo-text {
    font-size: 1.25rem;
  }

  .nav-link {
    font-size: 1rem;
    padding: 0.5rem 0.75rem;
  }
}
</style>
