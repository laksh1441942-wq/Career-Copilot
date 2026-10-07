class User {
  private city: string = "New York";
  email: string;
  UserId: number;
  constructor(email: string, UserId: number) {
    this.email = email;
    this.UserId = UserId;
  }
  get getCity(): string {
    return this.city;
  }
  set setcity(city: string) {
    this.city = city;
  }
}
let user1 = new User("lol@.com", 1);
user1.email = "newemail@.com";
let city1 = user1.getCity;
user1.setcity = "Los Angeles";
let city2 = user1.getCity;
console.log(city1);
console.log(city2);
