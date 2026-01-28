import numpy as np
from matplotlib import pyplot as plt

class aircraft:
    def __init__(self, character: dict) -> None:
        self.target_R = 8000                #目标航程/km
        self.Wto = 154760.                  #起飞总重/kg
        self.empty = 0.45                   #空重系数
        self.LD = 8.4                       #升阻比
        self.SFC = 0.11                     #耗油率/(kg/Nh)
        self.Velocity = 531.126             #巡航速度/(m/s)
        self.payload = 160*80               #有效载重/kg
        self.fuel = 72.3*1000               #燃油质量/kg
        self.extra_money = 100*1000         #固定成本(基建等)
        self.cost = 1                       #每座每千米成本(运营成本评估标准)
        self.h2_volume = 0                  #储氢罐体积
        self.Hmr = 0.8                      #液氢质量系数

        existing_attributes = self.__dict__.keys()
        for key, input_value in character.items():
            if key in existing_attributes:
                setattr(self, key, input_value)
            else:
                # 可选：抛出警告，提示传入了无效参数
                print(f"警告：传入了无效参数 '{key}'，已忽略")

        self.h2_mass = 70.96*self.h2_volume #储氢罐质量
        self.SFC_h2 = self.SFC * 43.1/120   #液氢热值为120MJ/kg, 航空燃油热值43.1MJ/kg
        self.range_h2 = self.Breguet("h2")  # 液氢能覆盖的航程（km，固定值）

    def inv_Breguet(self) -> float:
        """
        反布雷盖航程公式，求解指定航程下的需要的燃油质量
        
        :param self: 说明
        :return: 燃油质量
        :rtype: float
        """
        R = self.target_R
        V = self.Velocity
        C = self.SFC/3.6
        LD = self.LD
        W1 = self.Wto/np.exp(R*C*9.8/(V*LD))

        return self.Wto - W1
    
    def Breguet(self, fuel_type: str = "fuel") -> float:
        """
        布雷盖航程公式，已知燃油质量求解航程
        
        :param self: 说明
        :param fuel_type: 选用的燃料种类
        :return: 可行的航程
        :rtype: float
        """
        if fuel_type == "h2":
            # 切换为液氢的SFC和燃料质量
            current_SFC = self.SFC_h2
            current_fuel = self.h2_mass
        elif fuel_type == "fuel":
            # 默认为航空燃油的SFC和燃料质量
            current_SFC = self.SFC
            current_fuel = self.fuel
        else:
            raise ValueError("不支持的燃料类型，仅支持 'fuel'（航空燃油）和 'h2'（液氢）")
        V = self.Velocity
        C = current_SFC/3.6
        LD = self.LD
        W0 = self.Wto
        W1 = W0 - current_fuel

        return (V*LD*np.log(W0/W1))/(C*9.8)

    def cost_pkm(self) -> float:
        total = self.fuel + self.extra_money
        R = self.target_R
        person = self.payload/80

        return total/(R*person)
    

    def update_weight(self, iter_max: int = 10, err: float = 10) -> None:
        # print("液氢覆盖的航程：", self.range_h2)
        self.target_R = self.target_R - self.range_h2
        for i in range(iter_max):
            self.Wto -= self.h2_mass
            # print(self.target_R, self.Wto)
            self.fuel = self.inv_Breguet()*1.15         #反布雷盖公式计算燃油质量
            # print(self.fuel)
            tmp_Wto = self.Wto
            other_W = self.payload + self.fuel + self.h2_mass
            self.Wto = (1/(1-self.empty))*other_W
            delta = abs(tmp_Wto - self.Wto)
            if delta < err:
                # print("成功收敛", "迭代轮数", i)
                break
        self.cost = self.cost_pkm()
    
def main():
    para_dict = {
        "target_R" : 8000, #目标航程
        "Wto" : 134760., #起飞总重
        "empty" : 0.45, #空重系数
        "LD" : 8.4, #升阻比
        "SFC" : 0.11, #耗油率
        "Velocity" : 531.126, #巡航速度
        "payload" : 160*80, #有效载重
        "fuel" : 72.3 * 1000, 
        "extra_money" : 100*1000,
        "h2_volume" : 40
    }
    aircraft_bwb = aircraft(para_dict)
    aircraft_bwb.update_weight()
    print(aircraft_bwb.Wto)
    print(aircraft_bwb.fuel)
    print(aircraft_bwb.h2_mass)

    extra_list = []; best_R = []
    for k in range(9):
        aircraft_bwb.extra_money = (60 + 10*(k))*1000
        extra_list.append(aircraft_bwb.extra_money)
        r_list = []; wei = []; cost_list = []
        for i in range(51):
            aircraft_bwb.target_R = 5000 + 100*i
            aircraft_bwb.update_weight()
            r_list.append(aircraft_bwb.target_R)
            wei.append(aircraft_bwb.Wto/1000)
            cost_list.append(aircraft_bwb.cost)
            plt.plot(r_list, cost_list)
        best_R.append(r_list[np.argmin(cost_list)])
        print(r_list[np.argmin(cost_list)])
    np.savetxt("range2weight.dat", np.stack([r_list, wei], axis=0).T)
    np.savetxt("range2cost.dat", np.stack([r_list, cost_list], axis=0).T)
    np.savetxt("range2best.dat", np.stack([extra_list, best_R], axis=0).T)


if __name__ == "__main__":
    main()
    plt.show()
        