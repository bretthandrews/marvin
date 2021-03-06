/*
* @Author: Brian Cherinka
* @Date:   2016-04-13 17:38:25
* @Last Modified by:   Brian
* @Last Modified time: 2016-04-26 18:12:18
*/

//
// Javascript object handling all things related to OpenLayers Map
//

'use strict';

class OLMap {

    // Constructor
    constructor(image) {
        if (image === undefined) {
            console.error('Must specify an input image to initialize a Map!');
        } else {
            this.image = image;
            this.staticimdiv = $('#staticimage')[0];
            this.mapdiv = $('#imagediv')[0];
            this.getImageSize();
            this.setProjection();
            this.setView();
            this.initMap();
            this.addDrawInteraction();
        }

    };

    // test print
    print() {
        console.log('We are now printing openlayers map');
    };

    // Get the natural size of the input static image
    getImageSize() {
        if (this.staticimdiv !== undefined) {
            this.imwidth = this.staticimdiv.naturalWidth;
            this.imheight = this.staticimdiv.naturalHeight;
        }
    };

    // Set the mouse position control
    setMouseControl() {
        var mousePositionControl = new ol.control.MousePosition({
            coordinateFormat: ol.coordinate.createStringXY(4),
            projection: 'EPSG:4326',
            // comment the following two lines to have the mouse position be placed within the map.
            //className: 'custom-mouse-position',
            //target: document.getElementById('mouse-position'),
            undefinedHTML: '&nbsp;'
        });
        return mousePositionControl;
    };

    // Set the image Projection
    setProjection() {
      this.extent = [0, 0, this.imwidth, this.imheight];
      this.projection = new ol.proj.Projection({
        code: 'ifu',
        units: 'pixels',
        extent: this.extent
      });
    };

    // Set the base image Layer
    setBaseImageLayer() {
        var imagelayer = new ol.layer.Image({
            source: new ol.source.ImageStatic({
                url: this.image,
                projection: this.projection,
                imageExtent: this.extent
                })
        })
        return imagelayer;
    };

    // Set the image View
    setView() {
        this.view = new ol.View({
            projection: this.projection,
            center: ol.extent.getCenter(this.extent),
            zoom: 1,
            maxZoom: 8,
            maxResolution: 1.4
        })
    };

    // Initialize the Map
    initMap() {
        var mousePositionControl = this.setMouseControl();
        var baseimage = this.setBaseImageLayer();
        this.map = new ol.Map({
            controls: ol.control.defaults({
            attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
                collapsible: false
            })
            }).extend([mousePositionControl]),
            layers: [baseimage],
            target: this.mapdiv,
            view: this.view
        });
    };

    // Add a Draw Interaction
    addDrawInteraction() {
        // set up variable for last saved feature & vector source for point
        var lastFeature;
        var drawsource = new ol.source.Vector({wrapX: false});
        // create new point vectorLayer
        var pointVector = this.newVectorLayer(drawsource);
        // add the layer to the map
        this.map.addLayer(pointVector);

        // New draw event ; default to Point
        var value = 'Point';
        var geometryFunction, maxPoints;
        this.draw = new ol.interaction.Draw({
          source: drawsource,
          type: /** @type {ol.geom.GeometryType} */ (value),
          geometryFunction: geometryFunction,
          maxPoints: maxPoints
        });

        // On draw end, remove the last saved feature (point)
        this.draw.on('drawend', function(e) {
          if (lastFeature) {
            drawsource.removeFeature(lastFeature);
          }
          lastFeature = e.feature;
        });

        // add draw interaction onto the map
        this.map.addInteraction(this.draw);

    };

    // New Vector Layer
    newVectorLayer(source) {
        // default set to Point, but eventually expand this to different vector layer types
        var vector = new ol.layer.Vector({
            source: source,
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 255, 0.2)'
                }),
                stroke: new ol.style.Stroke({
                    color: '#FF0808',
                    width: 2
                }),
                image: new ol.style.Circle({
                    radius: 3,
                    fill: new ol.style.Fill({
                        color: '#FF0808'
                        })
                    })
            })
        });
        return vector;
    };

}

