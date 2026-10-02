"use strict";

/*
 * Responsive Landing Page Interaction Layer
 *
 * This file intentionally does not implement layout calculations.
 * CSS Grid, Flexbox, media queries, clamp(), and responsive sizing
 * are responsible for presentation. JavaScript manages runtime state:
 * the mobile navigation, keyboard behavior, and progressive form feedback.
 */

const BREAKPOINT_PX = 700;

const page = {
  menuToggle: document.querySelector(".menu-toggle"),
  navigation: document.querySelector("#primary-navigation"),
  navigationLinks: document.querySelectorAll("#primary-navigation a"),
  contactForm: document.querySelector("#contact-form"),
  formMessage: document.querySelector("#form-message"),
  year: document.querySelector("#year"),
};

function isMobileLayout() {
  return window.innerWidth < BREAKPOINT_PX;
}

function isNavigationOpen() {
  return page.menuToggle?.getAttribute("aria-expanded") === "true";
}

function setNavigationState(open) {
  if (!page.menuToggle || !page.navigation) {
    return;
  }

  page.navigation.classList.toggle("is-open", open);
  page.menuToggle.setAttribute("aria-expanded", String(open));
}

function toggleNavigation() {
  setNavigationState(!isNavigationOpen());
}

function closeNavigation() {
  setNavigationState(false);
}

function handleMenuToggle() {
  if (isMobileLayout()) {
    toggleNavigation();
  }
}

function handleNavigationLinkClick() {
  if (isMobileLayout()) {
    closeNavigation();
  }
}

function handleKeyboardNavigation(event) {
  if (event.key === "Escape" && isNavigationOpen()) {
    closeNavigation();
    page.menuToggle?.focus();
  }
}

function handleViewportChange() {
  /*
   * The desktop navigation is permanently visible through CSS.
   * Clearing the mobile state prevents an open mobile menu from leaving
   * stale ARIA state when the viewport crosses the responsive breakpoint.
   */
  if (!isMobileLayout()) {
    closeNavigation();
  }
}

function setCurrentYear() {
  if (page.year) {
    page.year.textContent = String(new Date().getFullYear());
  }
}

function validateEmailForm() {
  if (!page.contactForm || !page.formMessage) {
    return;
  }

  const formData = new FormData(page.contactForm);
  const rawEmail = formData.get("email");
  const email = typeof rawEmail === "string" ? rawEmail.trim() : "";

  if (!email) {
    page.formMessage.textContent = "Please enter an email address.";
    return;
  }

  /*
   * checkValidity() uses the HTML constraint system, including type="email"
   * and required. The browser remains responsible for enforcing the basic
   * input syntax, while JavaScript controls the page-specific response.
   */
  if (!page.contactForm.checkValidity()) {
    page.formMessage.textContent = "Please enter a valid email address.";
    page.contactForm.reportValidity();
    return;
  }

  /*
   * This demonstration deliberately does not transmit the address anywhere.
   * A real application must perform server-side validation before accepting
   * or storing submitted data.
   */
  page.formMessage.textContent = `Access request received for ${email}.`;
  page.contactForm.reset();
}

function initializeNavigation() {
  page.menuToggle?.addEventListener("click", handleMenuToggle);

  page.navigationLinks.forEach((link) => {
    link.addEventListener("click", handleNavigationLinkClick);
  });

  document.addEventListener("keydown", handleKeyboardNavigation);
  window.addEventListener("resize", handleViewportChange);
}

function initializeForm() {
  page.contactForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    validateEmailForm();
  });
}

function initializePage() {
  initializeNavigation();
  initializeForm();
  setCurrentYear();
}

initializePage();
