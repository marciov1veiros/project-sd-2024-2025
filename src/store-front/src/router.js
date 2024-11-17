import { createWebHistory, createRouter } from "vue-router";
import ProductList from "./components/ProductList.vue";
import ProductDetail from "./components/ProductDetail.vue";
import ShoppingCart from "./components/ShoppingCart.vue";

const routes = [
  { path: "/", component: ProductList },
  { path: "/product/:id", component: ProductDetail },
  { path: "/cart", component: ShoppingCart },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;