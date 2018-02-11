#!/usr/bin/python
# -*- coding: utf-8 -*-

import nmrglue as ng
import numpy as np
from collections import OrderedDict

from common import *
from observer import Observer
from spectrumDB import SpectrumDB

from customBoxSelect import CustomBoxSelect
from customTapTool import CustomTapTool
from tools.peakPickingSelectTool import PeakPickingSelectTool
from tools.peakByPeakTapTool import PeakByPeakTapTool

from widgets.customButton import CustomButton

from bokeh.models.sources import ColumnDataSource
from bokeh.models.widgets import Button, DataTable, TableColumn, Div, Paragraph, NumberFormatter, TextInput
from bokeh.models.callbacks import CustomJS
from bokeh.models.markers import Circle

class PeakPicking(Observer):

    def __init__(self, logger, spectrumId, dic, udic, pdata, dataSource, reference):
        Observer.__init__(self, logger)
        self.logger = logger
        self.id = spectrumId

        self.dic = dic
        self.udic = udic
        self.pdata = pdata
        self.mpdata = np.array(map(lambda x: -x, pdata))
        self.dataSource = dataSource

        reference.addObserver(lambda n: referenceObserver(self, n))

        self.sources = dict()
        self.sources['select'] = ColumnDataSource(data=dict(x=[], y=[], width=[], height=[]))
        self.sources['peaks'] = ColumnDataSource(data=dict(x=[], y=[]))

    def create(self):

        self.sources['table'] = ColumnDataSource(dict(x=[], y=[]))
        columns = [
                TableColumn(field="x", title="ppm", formatter=NumberFormatter(format="0.00")),
                TableColumn(field="y", title="y", formatter=NumberFormatter(format="0.00"))
            ]
        self.dataTable = DataTable(source=self.sources['table'], columns=columns, width=500)
        self.sources['table'].on_change('selected', lambda attr, old, new: self.rowSelect(new['1d']['indices']))
        self.sources['table'].on_change('data', lambda attr, old, new: self.dataChanged(old, new))

        self.manual = CustomButton(label="Manual Peaks", button_type="success", width=500, error="Please select area using the peak picking tool.")
        self.manual.on_click(self.manualPeakPicking)

        self.peakInput = TextInput(title="Peak By Peak", width=550, disabled=True)
        self.peak = CustomButton(label="Peak By Peak", button_type="primary", width=250, error="Please select area using the peak by peak tool.")
        self.peak.on_click(self.peakPeakPicking)
        self.peakTool = CustomTapTool(self.logger, self.peakInput, self.peak, tapTool=PeakByPeakTapTool)

        self.manualTool = CustomBoxSelect(self.logger, self.sources['select'], self.manual, selectTool=PeakPickingSelectTool)

        self.createResetButton()
        self.createDeselectButton()
        self.createDeleteButton()

        self.chemicalShiftReportTitle = Div(text="<strong>Chemical Shift Report</strong>" if getLabel(self.udic) == "13C" else "")
        self.chemicalShiftReport = Paragraph(text=self.getChemicalShiftReport(), width=500)

    def dataChanged(self, old, new):

        added = list(set(new['x']) - set(old['x']))
        removed = list(set(old['x']) - set(new['x']))

        SpectrumDB.AddPeaks(self.id, added)
        SpectrumDB.RemovePeaks(self.id, removed)

        # Update Chemical Shift Report
        self.updateChemicalShiftReport()

    def updateChemicalShiftReport(self):
        self.chemicalShiftReport.text = self.getChemicalShiftReport()

    def getChemicalShiftReport(self):
        label = getLabel(self.udic)
        if label == "13C":
            return getMetadata(self.dic, self.udic) + " δ " + ", ".join("{:0.2f}".format(x) for x in [round(x, 2) for x in self.sources['table'].data['x']]) + "."
        else:
            return ""

    def createResetButton(self):
        self.resetButton = Button(label="Clear Selected Area", button_type="default", width=250)
        resetButtonCallback = CustomJS(args=dict(source=self.sources['select'], button=self.manual), code="""
            // get data source from Callback args
            var data = source.data;
            data['x'] = [];
            data['y'] = [];
            data['width'] = [];
            data['height'] = [];

            button.data = {};

            source.change.emit();
        """)
        self.resetButton.js_on_click(resetButtonCallback)

    def createDeselectButton(self):
        self.deselectButton = Button(label="Deselect all peaks", button_type="default", width=250)
        self.deselectButton.on_click(self.deselectData)

    def deselectData(self):
        self.sources['peaks'].data = dict(x=[], y=[])
        self.deselectRows()

    def createDeleteButton(self):
        self.ids = []
        self.deleteButton = Button(label="Delete selected peaks", button_type="danger", width=250)
        self.deleteButton.on_click(self.deletePeaks)

    def deletePeaks(self):
        self.sources['peaks'].data = dict(x=[], y=[])

        newX = list(self.sources['table'].data['x'])
        newY = list(self.sources['table'].data['y'])

        ids = self.sources['table'].selected['1d']['indices']
        for i in sorted(ids, reverse=True):
            try:
                newX.pop(i)
                newY.pop(i)
            except IndexError:
                pass

        self.sources['table'].data = {
            'x': newX,
            'y': newY
        }
        self.deselectRows()

        self.notifyObservers()

    def deselectRows(self):
        self.sources['table'].selected = {
            '0d': {'glyph': None, 'indices': []},
            '1d': {'indices': []},
            '2d': {'indices': {}}
        }

    def manualPeakPicking(self, dimensions):

        # Clear selected area
        self.sources['select'].data = dict(x=[], y=[], width=[], height=[])

        data = self.pdata
        if abs(dimensions['y0']) > abs(dimensions['y1']):
            data = self.mpdata

            # Swap and invert y-dimensions
            dimensions['y0'], dimensions['y1'] = -dimensions['y1'], -dimensions['y0']
        peaks = ng.peakpick.pick(data, dimensions['y0'], algorithm="downward")
        self.peaksIndices = [int(peak[0]) for peak in peaks]

        # Filter top
        self.peaksIndices = [i for i in self.peaksIndices if self.pdata[i] <= dimensions['y1']]
        # Filter left
        self.peaksIndices = [i for i in self.peaksIndices if self.dataSource.data['ppm'][i] <= dimensions['x0']]
        # Filter right
        self.peaksIndices = [i for i in self.peaksIndices if self.dataSource.data['ppm'][i] >= dimensions['x1']]

        if len(self.peaksIndices) > 0:
            self.updateDataValues()
            self.notifyObservers()

    def peakPeakPicking(self, dimensions):

        data = {
            'x': [dimensions['x']],
            'y': [self.pdata[np.abs(self.dataSource.data['ppm'] - dimensions['x']).argmin()]]
        }
        self.sources['table'].stream(data)
        self.notifyObservers()

    def updateDataValues(self):
        # Update DataTable Values
        newData = list(OrderedDict.fromkeys(
            zip(
                self.sources['table'].data['x'] + [self.dataSource.data['ppm'][i] for i in self.peaksIndices],
                self.sources['table'].data['y'] + [self.pdata[i] for i in self.peaksIndices]
            )
        ))
        newX, newY = zip(*sorted(newData, reverse=True))
        self.sources['table'].data = {
            'x': newX,
            'y': newY
        }

    def rowSelect(self, ids):
        self.sources['peaks'].data = {
            'x': [self.sources['table'].data['x'][i] for i in ids],
            'y': [self.sources['table'].data['y'][i] for i in ids]
        }

    def rowSelectFromPeaks(self, ids):
        self.sources['peaks'].data = {
            'x': [self.dataSource.data['ppm'][i] for i in ids],
            'y': [self.pdata[i] for i in ids]
        }

    def getPeaksInSpace(self, start, stop):
        return [y for x, y in zip(self.sources['table'].data['x'], self.sources['table'].data['y']) if x <= start and x >= stop]

    def getPPMInSpace(self, start, stop):
        return [x for x in self.sources['table'].data['x'] if x <= start and x >= stop]

    def draw(self, plot):
        circle = Circle(
            x="x",
            y="y",
            size=10,
            line_color="#ff0000",
            fill_color="#ff0000",
            line_width=1
        )
        plot.add_glyph(self.sources['peaks'], circle, selection_glyph=circle, nonselection_glyph=circle)

        self.manualTool.addToPlot(plot)
        self.manualTool.addGlyph(plot, "#009933")

        self.peakTool.addToPlot(plot)
