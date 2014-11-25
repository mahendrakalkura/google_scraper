var application = angular.module('application', []);

application.config(function ($httpProvider, $interpolateProvider) {
    $httpProvider.defaults.headers.post[
        'Content-Type'
    ] = 'application/x-www-form-urlencoded';
    $interpolateProvider.startSymbol('[!').endSymbol('!]');
});

application.controller('memories', function ($attrs, $http, $scope) {
    var render = function () {
        var get_width = function () {
            return jQuery('#memories_highcharts').parent().width();
        };

        var chart = new window.Highcharts.Chart({
            chart: {
                renderTo: 'memories_highcharts',
                type: 'line',
                width: get_width()
            },
            credits: {
                enabled: false
            },
            exporting: {
                enabled: false
            },
            labels: {
                style: {
                    color: '#333'
                }
            },
            loading: false,
            plotOptions: {
                line: {
                    dataLabels: {
                        enabled: true,
                        rotation: 45,
                        style: {
                            color: '#333'
                        }
                    },
                    enableMouseTracking: false
                }
            },
            series: $scope.series,
            size: {},
            title: {
                style: {
                    color: '#333'
                },
                text: false
            },
            xAxis: {
                categories: $scope.x_axis_categories,
                gridLineColor: '#ddd',
                labels: {
                    rotation: 90,
                    style: {
                        color: '#333'
                    }
                }
            },
            yAxis: {
                gridLineColor: '#ddd',
                labels: {
                    style: {
                        color: '#333'
                    }
                },
                title: {
                    style: {
                        color: '#333'
                    },
                    text: 'MB'
                }
            }
        });

        jQuery(window).resize(function () {
            chart.setSize(get_width(), 500);
        });
    };

    $scope.series = [];
    $scope.x_axis_categories = [];

    $scope.spinner = true;
    $scope.success = false;
    $scope.failure = false;

    $scope.refresh = function () {
        $scope.spinner = true;
        $scope.success = false;
        $scope.failure = false;
        $http({
            method: 'POST',
            url: $attrs.url
        }).error(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = false;
            $scope.failure = true;
        }).success(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = true;
            $scope.failure = false;
            $scope.series = data.series;
            $scope.x_axis_categories = data.x_axis_categories;
            render();
        });
    };

    $scope.refresh();
});

application.controller('proxies', function ($attrs, $http, $scope) {
    $scope.proxies = '';
    $scope.proxies_sources = '';
    $scope.proxies_non_sources = '';
    $scope.proxies_non_sources_banned = '';
    $scope.proxies_non_sources_used = '';
    $scope.proxies_non_sources_unused = '';
    $scope.last_updated_on = '';

    $scope.spinner = true;
    $scope.success = false;
    $scope.failure = false;

    $scope.refresh = function () {
        $scope.spinner = true;
        $scope.success = false;
        $scope.failure = false;
        $http({
            method: 'POST',
            url: $attrs.url
        }).error(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = false;
            $scope.failure = true;
        }).success(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = true;
            $scope.failure = false;
            $scope.proxies = data.proxies;
            $scope.proxies_sources = data.proxies_sources;
            $scope.proxies_non_sources = data.proxies_non_sources;
            $scope.proxies_non_sources_banned = data.proxies_non_sources_banned;
            $scope.proxies_non_sources_used = data.proxies_non_sources_used;
            $scope.proxies_non_sources_unused = data.proxies_non_sources_unused;
            $scope.last_updated_on = data.last_updated_on;
        });
    };

    $scope.refresh();
});

application.controller('requests', function ($attrs, $http, $scope) {
    var render = function () {
        var get_width = function () {
            return jQuery(
                '#statistics_requests_status_code_highcharts'
            ).parent().width();
        };

        var chart_1 = new window.Highcharts.Chart({
            chart: {
                renderTo: 'statistics_requests_status_code_highcharts',
                width: get_width()
            },
            credits: {
                enabled: false
            },
            exporting: {
                enabled: false
            },
            loading: false,
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false,
                        format:
                        '<strong>{point.name}</strong>: {point.percentage:.1f} %',
                        style: {
                            color: (
                                Highcharts.theme
                                &&
                                Highcharts.theme.contrastTextColor
                            ) || 'black'
                        }
                    },
                    showInLegend: true
                }
            },
            series: [{
                data: $scope.status_codes,
                name: 'Status Codes',
                type: 'pie'
            }],
            title: {
                text: false
            },
            tooltip: {
                pointFormat: '{point.percentage:.2f}%</b>'
            }
        });

        var chart_2 = new window.Highcharts.Chart({
            chart: {
                renderTo: 'statistics_requests_has_captcha_highcharts',
                width: get_width()
            },
            credits: {
                enabled: false
            },
            exporting: {
                enabled: false
            },
            loading: false,
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false,
                        format:
                        '<strong>{point.name}</strong>: {point.percentage:.1f} %',
                        style: {
                            color: (
                                Highcharts.theme
                                &&
                                Highcharts.theme.contrastTextColor
                            ) || 'black'
                        }
                    },
                    showInLegend: true
                }
            },
            series: [{
                data: $scope.has_captchas,
                name: 'Status Codes',
                type: 'pie'
            }],
            title: {
                text: false
            },
            tooltip: {
                pointFormat: '{point.percentage:.2f}%</b>'
            }
        });

        jQuery(window).resize(function () {
            chart_1.setSize(get_width(), 350);
            chart_2.setSize(get_width(), 350);
        });
    };

    $scope.status_codes = [];
    $scope.has_captchas = [];
    $scope.requests = '';
    $scope.requests_per_day = '';
    $scope.requests_per_hour = '';
    $scope.requests_per_minute = '';
    $scope.requests_per_second = '';
    $scope.durations_minimum = '';
    $scope.durations_maximum = '';
    $scope.durations_mean = '';
    $scope.durations_median = '';
    $scope.durations_mode = '';
    $scope.last_updated_on = '';

    $scope.spinner = true;
    $scope.success = false;
    $scope.failure = false;

    $scope.refresh = function () {
        $scope.spinner = true;
        $scope.success = false;
        $scope.failure = false;
        $http({
            method: 'POST',
            url: $attrs.url
        }).error(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = false;
            $scope.failure = true;
        }).success(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = true;
            $scope.failure = false;
            $scope.status_codes = data.status_codes;
            $scope.has_captchas = data.has_captchas;
            $scope.requests = data.requests;
            $scope.requests_per_day = data.requests_per_day;
            $scope.requests_per_hour = data.requests_per_hour;
            $scope.requests_per_minute = data.requests_per_minute;
            $scope.requests_per_second = data.requests_per_second;
            $scope.durations_minimum = data.durations_minimum;
            $scope.durations_maximum = data.durations_maximum;
            $scope.durations_mean = data.durations_mean;
            $scope.durations_median = data.durations_median;
            $scope.durations_mode = data.durations_mode;
            $scope.last_updated_on = data.last_updated_on;
            render();
        });
    };

    $scope.refresh();
});

application.controller('results', function ($attrs, $http, $scope) {
    $scope.results = '';
    $scope.results_per_day = '';
    $scope.results_per_hour = '';
    $scope.results_per_minute = '';
    $scope.results_per_second = '';
    $scope.last_updated_on = '';

    $scope.spinner = true;
    $scope.success = false;
    $scope.failure = false;

    $scope.refresh = function () {
        $scope.spinner = true;
        $scope.success = false;
        $scope.failure = false;
        $http({
            method: 'POST',
            url: $attrs.url
        }).error(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = false;
            $scope.failure = true;
        }).success(function (data, status, headers, config) {
            $scope.spinner = false;
            $scope.success = true;
            $scope.failure = false;
            $scope.results = data.results;
            $scope.results_per_day = data.results_per_day;
            $scope.results_per_hour = data.results_per_hour;
            $scope.results_per_minute = data.results_per_minute;
            $scope.results_per_second = data.results_per_second;
            $scope.last_updated_on = data.last_updated_on;
        });
    };

    $scope.refresh();
});
