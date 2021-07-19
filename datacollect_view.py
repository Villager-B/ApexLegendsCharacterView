import os
import sys
import json
import re
import math
import requests
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time
import japanize_matplotlib
import pandas as pd
import pickle

base_url = "https://public-api.tracker.gg/v2/apex/standard/"
params = {"TRN-Api-Key":"XXX"} # You API key
endpoint = "profile/origin/shimasan0x00" # You Origin name . if PSN -> progile/psn/XXX

co = [
    '#7f605a',
    '#a28a5b',
    '#d0ab35',
    '#c7de51',
    '#d5a55c',
    '#bdbdb9',
    '#b4d3bd',
    '#b65454',
    '#c7c5c2',
    '#d9b628',
    '#797532',
    '#4f6f7b',
    '#db5445',
    '#904a49',
    '#6f8ba1',
    '#504b5f'
]



session = requests.Session()
req = session.get(base_url+endpoint,params=params)
req.close()

res = json.loads(req.text)

col = [
    "date",
    'legend_id',
    'name',
    'play_count',
    'expiry_date',
    'img_url'
]

# DataFrame Load/Create

try:
    with open("apex_stats.pkl", "rb") as f:
        df = pickle.load(f)
except BaseException:
    df = pd.DataFrame(columns=col)

now = datetime.datetime.today()
d1 = str(now.year) + "-" + str(now.month) + "-" + \
    str(now.day)

for item in res['data']['segments']:
    if not item.get('attributes'):
        continue
        
    legend_id = item['attributes']['id']
    name = item['metadata']['name']
    try:
        play_count = int(item['stats']['matchesPlayed']['displayValue'])
    except:
        print(name,'not play')
        play_count = 0
    
    expiry_date = item['expiryDate']
    img_url = item['metadata']['imageUrl']
    
    df_line = pd.DataFrame([[d1,
                             legend_id,
                             name,
                             play_count,
                             expiry_date,
                             img_url
                            ]],
                       columns=col)

    df = df.append(df_line, ignore_index=True)
    
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('name',ascending=True)

with open('apex_df.pkl','wb') as f:
    pickle.dump(df,f)
    
class BubbleChart:
    def __init__(self, area, bubble_spacing=0):
        """
        Setup for bubble collapse.

        Parameters
        ----------
        area : array-like
            Area of the bubbles.
        bubble_spacing : float, default: 0
            Minimal spacing between bubbles after collapsing.

        Notes
        -----
        If "area" is sorted, the results might look weird.
        """
        area = np.asarray(area)
        r = np.sqrt(area / np.pi)

        self.bubble_spacing = bubble_spacing
        self.bubbles = np.ones((len(area), 4))
        self.bubbles[:, 2] = r
        self.bubbles[:, 3] = area
        self.maxstep = 2 * self.bubbles[:, 2].max() + self.bubble_spacing
        self.step_dist = self.maxstep / 2

        # calculate initial grid layout for bubbles
        length = np.ceil(np.sqrt(len(self.bubbles)))
        grid = np.arange(length) * self.maxstep
        gx, gy = np.meshgrid(grid, grid)
        self.bubbles[:, 0] = gx.flatten()[:len(self.bubbles)]
        self.bubbles[:, 1] = gy.flatten()[:len(self.bubbles)]

        self.com = self.center_of_mass()

    def center_of_mass(self):
        return np.average(
            self.bubbles[:, :2], axis=0, weights=self.bubbles[:, 3]
        )

    def center_distance(self, bubble, bubbles):
        return np.hypot(bubble[0] - bubbles[:, 0],
                        bubble[1] - bubbles[:, 1])

    def outline_distance(self, bubble, bubbles):
        center_distance = self.center_distance(bubble, bubbles)
        return center_distance - bubble[2] - \
            bubbles[:, 2] - self.bubble_spacing

    def check_collisions(self, bubble, bubbles):
        distance = self.outline_distance(bubble, bubbles)
        return len(distance[distance < 0])

    def collides_with(self, bubble, bubbles):
        distance = self.outline_distance(bubble, bubbles)
        idx_min = np.argmin(distance)
        return idx_min if type(idx_min) == np.ndarray else [idx_min]

    def collapse(self, n_iterations=50):
        """
        Move bubbles to the center of mass.

        Parameters
        ----------
        n_iterations : int, default: 50
            Number of moves to perform.
        """
        for _i in range(n_iterations):
            moves = 0
            for i in range(len(self.bubbles)):
                rest_bub = np.delete(self.bubbles, i, 0)
                # try to move directly towards the center of mass
                # direction vector from bubble to the center of mass
                dir_vec = self.com - self.bubbles[i, :2]

                # shorten direction vector to have length of 1
                dir_vec = dir_vec / np.sqrt(dir_vec.dot(dir_vec))

                # calculate new bubble position
                new_point = self.bubbles[i, :2] + dir_vec * self.step_dist
                new_bubble = np.append(new_point, self.bubbles[i, 2:4])

                # check whether new bubble collides with other bubbles
                if not self.check_collisions(new_bubble, rest_bub):
                    self.bubbles[i, :] = new_bubble
                    self.com = self.center_of_mass()
                    moves += 1
                else:
                    # try to move around a bubble that you collide with
                    # find colliding bubble
                    for colliding in self.collides_with(new_bubble, rest_bub):
                        # calculate direction vector
                        dir_vec = rest_bub[colliding, :2] - self.bubbles[i, :2]
                        dir_vec = dir_vec / np.sqrt(dir_vec.dot(dir_vec))
                        # calculate orthogonal vector
                        orth = np.array([dir_vec[1], -dir_vec[0]])
                        # test which direction to go
                        new_point1 = (self.bubbles[i, :2] + orth *
                                      self.step_dist)
                        new_point2 = (self.bubbles[i, :2] - orth *
                                      self.step_dist)
                        dist1 = self.center_distance(
                            self.com, np.array([new_point1]))
                        dist2 = self.center_distance(
                            self.com, np.array([new_point2]))
                        new_point = new_point1 if dist1 < dist2 else new_point2
                        new_bubble = np.append(new_point, self.bubbles[i, 2:4])
                        if not self.check_collisions(new_bubble, rest_bub):
                            self.bubbles[i, :] = new_bubble
                            self.com = self.center_of_mass()

            if moves / len(self.bubbles) < 0.1:
                self.step_dist = self.step_dist / 2

    def plot(self, ax, labels, colors):
        """
        Draw the bubble plot.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
        labels : list
            Labels of the bubbles.
        colors : list
            Colors of the bubbles.
        """
        for i in range(len(self.bubbles)):
            circ = plt.Circle(
                self.bubbles[i, :2], self.bubbles[i, 2], color=colors[i])
            ax.add_patch(circ)
            ax.text(*self.bubbles[i, :2], labels[i],
                    horizontalalignment='center', verticalalignment='center',fontsize=20)


names = df['name'].tolist()
counts = df['play_count'].tolist()
counts = [int(x) for x in counts]

color_l = co

bubble_chart = BubbleChart(area=counts,
                           bubble_spacing=0.1)

bubble_chart.collapse()

plt.style.use('dark_background')
fig, ax = plt.subplots(subplot_kw=dict(aspect="equal"),figsize=(16, 10), dpi=100)
bubble_chart.plot(
    ax, names, color_l)


ax.axis("off")
ax.relim()
ax.autoscale_view()

ax.set_title('Percentage of Legends Used',fontsize=30)

plt.savefig('result.jpg')
plt.show()
