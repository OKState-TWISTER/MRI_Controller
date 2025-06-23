import numpy as np

class Point:
    def __init__(self, az, el):
        self.az = az
        self.el = el
        self.el_ideal = el
        self.peak_freq = np.NaN
        self.peak_val = np.NaN
        self.idx = -1
    
    def addReading(self, peak_val, peak_freq):
        self.peak_val = peak_val
        self.peak_freq = peak_freq

    def set_el(self, el):
        self.el = el



class Grid:
    def __init__(self, el_start, el_stop, el_step, az_start, az_stop, az_step):
        self.el_start = el_start
        self.el_stop = el_stop
        self.el_step = el_step
        self.az_start = az_start
        self.az_stop = az_stop
        self.az_step = az_step

        rows = int(round((el_stop - el_start)/el_step)) + 1
        cols = int(round((az_stop - az_start)/az_step)) + 1

        self.grid = []
        
        for i in range(rows):
            tempRow = []
            for j in range(cols):
                az = self.az_start + (j * self.az_step)
                el = self.el_start + (i * self.el_step)
                tempRow.append(Point(az, el))
            self.grid.append(tempRow)
        self.grid = np.asarray(self.grid)

    def get_serpentine(self):
        temp_grid = np.copy(self.grid)

        temp_grid[1::2] = temp_grid[1::2, ::-1]
        temp_grid = temp_grid.reshape((1, np.size(temp_grid)))
        return temp_grid[0]
    
    def get_grid_order(self):
        temp_grid = np.copy(self.grid)

        temp_grid = temp_grid.reshape((1, np.size(temp_grid)))
        return temp_grid[0]
    
    def _get_az_angle(self, val):
        return val.az

    def get_az_angle_grid(self):
        gpv = np.vectorize(self._get_az_angle)
        # return np.apply_along_axis(self._get_peak_val, 0, self.grid)
        return gpv(self.grid)
    
    def _get_el_angle(self, val):
        return val.el

    def get_el_angle_grid(self):
        gpv = np.vectorize(self._get_el_angle)
        # return np.apply_along_axis(self._get_peak_val, 0, self.grid)
        return gpv(self.grid)
    
    def _get_peak_val(self, val):
        return val.peak_val

    def get_peak_val_grid(self):
        gpv = np.vectorize(self._get_peak_val)
        # return np.apply_along_axis(self._get_peak_val, 0, self.grid)
        return gpv(self.grid)
    
    def _get_peak_freq(self, val):
        return val.peak_freq

    def get_peak_freq_grid(self):
        gpv = np.vectorize(self._get_peak_freq)
        # return np.apply_along_axis(self._get_peak_val, 0, self.grid)
        return gpv(self.grid)
    
    def _get_idx(self, val):
        return val.idx

    def get_idx_grid(self):
        gpv = np.vectorize(self._get_idx)
        # return np.apply_along_axis(self._get_peak_val, 0, self.grid)
        return gpv(self.grid)
    
    def get_point_by_travel_order(self, index):
        return self.get_serpentine()[index]
    
    def get_point_by_grid_order(self, index):
        return self.get_grid_order()[index]


if __name__ == "__main__":
    g = Grid(-0.2, 0.2, 0.2, -0.2, 0.2, 0.2)
    for i in range(len(g.grid)):
        print()
        for j in range(len(g.grid[i])):
            print(f"{g.grid[i][j].az:.2f}x{g.grid[i][j].el:.2f}",end="\t")
    temp_grid = g.get_serpentine()
    for i in range(temp_grid.size):
        print(temp_grid[i].az)
    # print()
    # print(np.shape(temp_grid))
    # print(temp_grid)
    # for i in range(np.size(temp_grid)):
    #     print(f"{temp_grid[i].az:.2f}x{temp_grid[i].el:.2f}", end="\t")
    # print()

    temp_grid[0].set_el(12.34)

    g.get_point_by_travel_order(1).addReading(1, 1)
    g.get_point_by_travel_order(2).addReading(2, 2)
    g.get_point_by_travel_order(3).addReading(3, 3)
    g.get_point_by_travel_order(4).addReading(4, 4)
    g.get_point_by_travel_order(8).addReading(8, 8)

    print(g.get_el_angle_grid())
    print(g.get_peak_val_grid())
    
