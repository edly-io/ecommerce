define([
    'backbone',
    'routers/page_router',
    'pages/subscription_create_page',
    'pages/subscription_detail_page',
    'pages/subscription_edit_page',
    'pages/subscription_list_page',
    'underscore'
],
    function(Backbone,
             PageRouter,
             SubscriptionCreatePage,
             SubscriptionDetailPage,
             SubscriptionEditPage,
             SubscriptionListPage,
             _) {
        'use strict';

        return PageRouter.extend({
            // Base/root path of the app
            root: '/subscriptions/',

            routes: {
                '(/)': 'index',
                'new(/)': 'new',
                ':id(/)': 'show',
                ':id/edit(/)': 'edit',
                '*path': 'notFound'
            },

            getListPage: function() {
                return new SubscriptionListPage();
            },

            getCreatePage: function() {
                return new SubscriptionCreatePage();
            },

            getDetailPage: function(id) {
                return new SubscriptionDetailPage({id: id});
            },

            getEditPage: function(id) {
                return new SubscriptionEditPage({id: id});
            },

            /**
             * Display a list of all subscriptions in the system.
             */
            index: function() {
                var page = this.getListPage();
                this.currentView = page;
                this.$el.html(page.el);
            },

            new: function() {
                var page = this.getCreatePage();
                this.currentView = page;
                this.$el.html(page.el);
            },

            show: function(id) {
                var page = this.getDetailPage(id);
                this.currentView = page;
                this.$el.html(page.el);
            },

            edit: function(id) {
                var page = this.getEditPage(id);
                this.currentView = page;
                this.$el.html(page.el);
            }
        });
    }
);
