/*
* @Author: Brian Cherinka
* @Date:   2016-12-09 01:38:32
* @Last Modified by:   Brian Cherinka
* @Last Modified time: 2016-12-09 11:38:05
*/

'use strict';

// Creates a Scatter Plot Highcharts Object

class Scatter {

    // Constructor
    constructor(id, data, options) {
        if (data === undefined) {
            console.error('Must specify input plot data to initialize a ScatterPlot!');
        } else if (id === undefined) {
            console.error('Must specify an input plotdiv to initialize a ScatterPlot');
        } else {
            this.plotdiv = id; // div element for map
            this.data = data; // map data
            //this.title = title; // map title
            //this.origthis = galthis; //the self of the Galaxy class
            //this.parseTitle();
            this.setOptions(options);
            this.initChart();
        }

    };

    // test print
    print() {
        console.log('We are now printing scatter for ', this.cfg.title);
    };

    // sets the options
    setOptions(options) {
        // create the default options
        this.cfg = {
            title:'Scatter Title',
            origthis:null
        };

        //Put all of the options into a variable called cfg
        if('undefined' !== typeof options){
          for(var i in options){
            if('undefined' !== typeof options[i]){ this.cfg[i] = options[i]; }
          }
        }
    }

    // initialize the chart
    initChart() {
        console.log('init plotdiv', this.plotdiv.attr('id'));
    this.plotdiv.empty();
    this.chart = Highcharts.chart(this.plotdiv.attr('id'), {
        chart: {
            type: 'scatter',
            zoomType: 'xy',
            backgroundColor: '#F5F5F5',
            plotBackgroundColor: '#F5F5F5'
        },
        title: {
            text: 'NSA redshift vs Stellar Mass'
        },
        xAxis: {
            title: {
                enabled: true,
                text: 'Stellar Mass'
            },
            startOnTick: true,
            endOnTick: true,
            showLastLabel: true,
            id: 'mass-axis'
        },
        yAxis: {
            title: {
                text: 'NSA z'
            },
            id: 'nsaz-axis'
        },
        legend: {
            layout: 'vertical',
            align: 'left',
            verticalAlign: 'top',
            x: 100,
            y: 70,
            floating: true,
            backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
            borderWidth: 1
        },
        plotOptions: {
            scatter: {
                marker: {
                    radius: 5,
                    states: {
                        hover: {
                            enabled: true,
                            lineColor: 'rgb(100,100,100)'
                        }
                    }
                },
                states: {
                    hover: {
                        marker: {
                            enabled: false
                        }
                    }
                },
                tooltip: {
                    headerFormat: '<b>{series.name}</b><br>',
                    pointFormat: '({point.x} M*, {point.y})'
                }
            }
        },
        series: [
        // {
        //     name: 'Sample',
        //     color: 'rgba(70,130,180,0.4)',
        //     data: grz,
        //     turboThreshold:0,
        //     marker: {
        //         radius:2,
        //         symbol: 'circle'
        //     },
        //         tooltip: {
        //             headerFormat: '<b>{series.name}: {point.key}</b><br>'                }

        // },
        {
            name: '8485-1901',
            color: 'rgba(255, 0, 0, 1)',
            data: this.data,
            marker: {symbol:'circle', radius:5}
        }]
    });
    }

}
